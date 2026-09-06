// workbench-api — Go control plane for the Sovereign Agentic AI Workbench.
package main

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
	"github.com/redis/go-redis/v9"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/ask"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/config"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/db"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/documents"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/httpapi"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/migrate"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/tasks"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/users"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/workspaces"
)

func main() {
	if err := run(); err != nil {
		slog.Error("fatal", "err", err)
		os.Exit(1)
	}
}

func run() error {
	cfg, err := config.Load()
	if err != nil {
		return err
	}
	level := slog.LevelInfo
	if cfg.LogLevel == "debug" {
		level = slog.LevelDebug
	}
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: level})))
	slog.Info("starting workbench-api", "env", cfg.Env)

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	pool, err := db.Connect(ctx, cfg.DatabaseURL)
	if err != nil {
		return err
	}
	defer pool.Close()

	applied, err := migrate.Apply(ctx, db.Pool{Pool: pool}, cfg.MigrationsDir)
	if err != nil {
		return err
	}
	if len(applied) > 0 {
		slog.Info("migrations applied", "count", len(applied), "files", applied)
	}

	redisOpts, err := redis.ParseURL(cfg.RedisURL)
	if err != nil {
		return err
	}
	rdb := redis.NewClient(redisOpts)
	defer rdb.Close()

	// --- identity: bootstrap admin, then auth service + routes ---
	auditRec := audit.NewRecorder(pool)
	userStore := users.NewStore(pool)
	authSvc := auth.NewService(userStore, auditRec, cfg.JWTSecret, cfg.TokenTTL)

	created, err := authSvc.BootstrapAdmin(ctx, cfg.BootstrapAdminEmail, cfg.BootstrapAdminPass, "Platform Admin")
	if err != nil {
		return err
	}
	if created {
		slog.Info("bootstrap admin created", "email", cfg.BootstrapAdminEmail)
	}

	ginMode := ginModeFor(cfg.Env)
	srv := httpapi.NewServer(ginMode)
	srv.AddRequired(httpapi.CheckerFunc{N: "postgres", F: pool.Ping})
	srv.AddRequired(httpapi.CheckerFunc{N: "redis", F: func(c context.Context) error {
		return rdb.Ping(c).Err()
	}})
	srv.AddOptional(httpapi.CheckerFunc{N: "ai_service", F: func(c context.Context) error {
		req, err := http.NewRequestWithContext(c, http.MethodGet, cfg.AIServiceURL+"/healthz", nil)
		if err != nil {
			return err
		}
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			return errors.New("ai service healthz returned " + resp.Status)
		}
		return nil
	}})

	engine := srv.Router()

	// /api/v1/auth/login is public; everything in the protected group
	// requires a valid bearer token. Future features mount here.
	publicAPI := engine.Group("/api/v1")
	protectedAPI := engine.Group("/api/v1", auth.Middleware(cfg.JWTSecret))
	auth.RegisterRoutes(publicAPI, protectedAPI, authSvc)
	wsHandler := workspaces.NewHandler(workspaces.NewStore(pool), auditRec)
	wsHandler.Register(protectedAPI)

	minioClient, err := minio.New(strings.TrimPrefix(cfg.S3Endpoint, "http://"), &minio.Options{
		Creds:  credentials.NewStaticV4(cfg.S3AccessKey, cfg.S3SecretKey, ""),
		Secure: false,
	})
	if err != nil {
		return fmt.Errorf("minio client: %w", err)
	}
	docStorage := &documents.MinioStorage{Client: minioClient, Bucket: cfg.S3Bucket}
	if err := docStorage.EnsureBucket(ctx); err != nil {
		slog.Warn("bucket ensure failed", "bucket", cfg.S3Bucket, "err", err)
	}
	aiSvc := ask.NewAIService(cfg.AIServiceURL, cfg.InternalAPISecret)
	docHandler := documents.NewHandler(documents.NewStore(pool), docStorage, auditRec)
	docHandler.Register(protectedAPI, wsHandler.RequireWsRole)
	docHandler.SetIngestTrigger(func() {
		if err := aiSvc.TriggerIngestion(context.Background()); err != nil {
			slog.Warn("ingestion trigger failed", "err", err)
		}
	})
	ask.NewHandler(aiSvc, auditRec).Register(protectedAPI, wsHandler.RequireWsRole)
	tasks.NewHandler(aiSvc, auditRec).Register(protectedAPI, wsHandler.RequireWsRole)

	httpServer := &http.Server{
		Addr:              ":" + cfg.APIPort,
		Handler:           engine,
		ReadHeaderTimeout: 10 * time.Second,
	}

	errCh := make(chan error, 1)
	go func() {
		slog.Info("api listening", "port", cfg.APIPort)
		errCh <- httpServer.ListenAndServe()
	}()

	select {
	case <-ctx.Done():
		slog.Info("shutdown signal received")
	case err := <-errCh:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			return err
		}
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return httpServer.Shutdown(shutdownCtx)
}

func ginModeFor(env string) string {
	if env == "production" {
		return "release"
	}
	return "debug"
}
