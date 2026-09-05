// workbench-api — Go control plane for the Sovereign Agentic AI Workbench.
package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/redis/go-redis/v9"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/config"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/db"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/httpapi"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/migrate"
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

	httpServer := &http.Server{
		Addr:              ":" + cfg.APIPort,
		Handler:           srv.Router(),
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
