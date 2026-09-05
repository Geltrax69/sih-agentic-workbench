//go:build integration

// Auth flow integration tests run against real PostgreSQL:
//
//	DATABASE_URL=postgres://... go test -tags=integration ./tests/integration/...
package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/db"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/migrate"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/users"
)

const testSecret = "integration-secret-0123456789abcdef0123456789abcdef"

func newAuthEnv(t *testing.T) (*gin.Engine, *users.Store) {
	t.Helper()
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		t.Skip("DATABASE_URL not set — skipping integration test")
	}
	ctx := context.Background()
	pool, err := db.Connect(ctx, dsn)
	if err != nil {
		t.Fatalf("connect: %v", err)
	}
	t.Cleanup(pool.Close)

	migrationDir := os.Getenv("MIGRATIONS_DIR")
	if migrationDir == "" {
		migrationDir = "../../../../migrations"
	}
	if _, err := migrate.Apply(ctx, db.Pool{Pool: pool}, migrationDir); err != nil {
		t.Fatalf("migrations: %v", err)
	}

	store := users.NewStore(pool)
	recorder := audit.NewRecorder(pool)
	svc := auth.NewService(store, recorder, testSecret, time.Hour)

	gin.SetMode(gin.TestMode)
	r := gin.New()
	auth.RegisterRoutes(
		r.Group("/api/v1"),
		r.Group("/api/v1", auth.Middleware(testSecret)),
		svc,
	)
	return r, store
}

func postJSON(r *gin.Engine, path string, body any) *httptest.ResponseRecorder {
	b, _ := json.Marshal(body)
	req := httptest.NewRequest(http.MethodPost, path, bytes.NewReader(b))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	return w
}

func getJSON(r *gin.Engine, path, bearer string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(http.MethodGet, path, nil)
	if bearer != "" {
		req.Header.Set("Authorization", "Bearer "+bearer)
	}
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	return w
}

// uniqueEmail avoids collisions in the persistent dev database.
func uniqueEmail() string {
	return fmt.Sprintf("auth-it-%d@test.local", time.Now().UnixNano())
}

func TestLoginFlow(t *testing.T) {
	r, store := newAuthEnv(t)
	ctx := context.Background()
	email := uniqueEmail()

	if _, err := store.Create(ctx, email, mustHash(t, "Sup3rSecret!pass"), "IT User", "member"); err != nil {
		t.Fatalf("seed user: %v", err)
	}

	t.Run("login succeeds with valid credentials", func(t *testing.T) {
		w := postJSON(r, "/api/v1/auth/login", map[string]string{"email": email, "password": "Sup3rSecret!pass"})
		if w.Code != http.StatusOK {
			t.Fatalf("code = %d, body = %s", w.Code, w.Body.String())
		}
		var body struct {
			Token string `json:"token"`
			User  struct {
				Email string `json:"email"`
				Role  string `json:"role"`
			} `json:"user"`
		}
		if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
			t.Fatal(err)
		}
		if body.Token == "" {
			t.Fatal("expected non-empty token")
		}
		if body.User.Email != email || body.User.Role != "member" {
			t.Fatalf("user payload mismatch: %+v", body.User)
		}

		// /auth/me accepts the fresh token.
		w = getJSON(r, "/api/v1/auth/me", body.Token)
		if w.Code != http.StatusOK {
			t.Fatalf("/auth/me code = %d, body = %s", w.Code, w.Body.String())
		}
	})

	t.Run("wrong password rejected with 401", func(t *testing.T) {
		w := postJSON(r, "/api/v1/auth/login", map[string]string{"email": email, "password": "WrongPassword1"})
		if w.Code != http.StatusUnauthorized {
			t.Fatalf("code = %d, want 401", w.Code)
		}
	})

	t.Run("unknown email rejected with 401", func(t *testing.T) {
		w := postJSON(r, "/api/v1/auth/login", map[string]string{"email": uniqueEmail(), "password": "Whatever123"})
		if w.Code != http.StatusUnauthorized {
			t.Fatalf("code = %d, want 401", w.Code)
		}
	})

	t.Run("malformed payload rejected with 400", func(t *testing.T) {
		w := postJSON(r, "/api/v1/auth/login", map[string]string{"email": "not-an-email", "password": "x"})
		if w.Code != http.StatusBadRequest {
			t.Fatalf("code = %d, want 400", w.Code)
		}
	})

	t.Run("auth/me without token rejected with 401", func(t *testing.T) {
		if w := getJSON(r, "/api/v1/auth/me", ""); w.Code != http.StatusUnauthorized {
			t.Fatalf("code = %d, want 401", w.Code)
		}
	})

	t.Run("login events audited", func(t *testing.T) {
		// The recorder writes resource_id = email for login events; the email
		// is unique per run, so counts are deterministic.
		p := poolFromEnv(t)
		var success, failure int
		if err := p.QueryRow(ctx,
			"SELECT count(*) FROM audit_events WHERE event_type = 'auth.login.success' AND resource_id = $1",
			email).Scan(&success); err != nil {
			t.Fatalf("audit query: %v", err)
		}
		if err := p.QueryRow(ctx,
			"SELECT count(*) FROM audit_events WHERE event_type = 'auth.login.failure' AND resource_id = $1",
			email).Scan(&failure); err != nil {
			t.Fatalf("audit query: %v", err)
		}
		if success < 1 {
			t.Errorf("expected >=1 auth.login.success audit event, got %d", success)
		}
		if failure < 1 {
			t.Errorf("expected >=1 auth.login.failure audit event (bad password), got %d", failure)
		}
	})
}

func mustHash(t *testing.T, plain string) string {
	t.Helper()
	h, err := auth.HashPassword(plain)
	if err != nil {
		t.Fatal(err)
	}
	return h
}

func poolFromEnv(t *testing.T) db.Pool {
	t.Helper()
	pool, err := db.Connect(context.Background(), os.Getenv("DATABASE_URL"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(pool.Close)
	return db.Pool{Pool: pool}
}
