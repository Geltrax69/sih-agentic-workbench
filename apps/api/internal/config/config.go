// Package config loads API configuration from the environment.
package config

import (
	"fmt"
	"os"
	"strings"
)

type Config struct {
	Env                  string
	LogLevel             string
	APIPort              string
	DatabaseURL          string
	RedisURL             string
	JWTSecret            string
	InternalAPISecret    string
	AIServiceURL         string
	S3Endpoint           string
	S3Bucket             string
	S3AccessKey          string
	S3SecretKey          string
	MigrationsDir        string
	BootstrapAdminEmail  string
	BootstrapAdminPass   string
}

func Load() (Config, error) {
	c := Config{
		Env:                 envOr("ENV", "development"),
		LogLevel:            envOr("LOG_LEVEL", "info"),
		APIPort:             envOr("API_PORT", "8080"),
		DatabaseURL:         os.Getenv("DATABASE_URL"),
		RedisURL:            envOr("REDIS_URL", "redis://localhost:6379/0"),
		JWTSecret:           os.Getenv("JWT_SECRET"),
		InternalAPISecret:   os.Getenv("INTERNAL_API_SECRET"),
		AIServiceURL:        envOr("AI_SERVICE_URL", "http://localhost:8000"),
		S3Endpoint:          envOr("S3_ENDPOINT", "http://localhost:9000"),
		S3Bucket:            envOr("S3_BUCKET", "workbench-documents"),
		S3AccessKey:         os.Getenv("S3_ACCESS_KEY"),
		S3SecretKey:         os.Getenv("S3_SECRET_KEY"),
		MigrationsDir:       envOr("MIGRATIONS_DIR", "./migrations"),
		BootstrapAdminEmail: envOr("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com"),
		BootstrapAdminPass:  os.Getenv("BOOTSTRAP_ADMIN_PASSWORD"),
	}

	if c.DatabaseURL == "" {
		return c, fmt.Errorf("DATABASE_URL is required")
	}
	if len(c.JWTSecret) < 32 {
		return c, fmt.Errorf("JWT_SECRET must be at least 32 bytes")
	}
	if c.InternalAPISecret == "" {
		return c, fmt.Errorf("INTERNAL_API_SECRET is required")
	}
	if c.Env == "production" && strings.Contains(c.JWTSecret, "dev-only") {
		return c, fmt.Errorf("JWT_SECRET must be changed from the development default")
	}
	return c, nil
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
