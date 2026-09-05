package httpapi

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

type stubChecker struct {
	n   string
	err error
}

func (s stubChecker) Name() string                  { return s.n }
func (s stubChecker) Check(_ context.Context) error { return s.err }

func performHealth(t *testing.T, s *Server) (int, map[string]any) {
	t.Helper()
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	w := httptest.NewRecorder()
	s.Router().ServeHTTP(w, req)

	var body map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid JSON body: %v — %s", err, w.Body.String())
	}
	return w.Code, body
}

func TestHealthAllUp(t *testing.T) {
	s := NewServer(gin.TestMode)
	s.AddRequired(stubChecker{n: "postgres"})
	s.AddOptional(stubChecker{n: "ai"})

	code, body := performHealth(t, s)
	if code != http.StatusOK {
		t.Fatalf("code = %d, want 200", code)
	}
	if body["status"] != "ok" {
		t.Fatalf("status = %v, want ok", body["status"])
	}
}

func TestHealthRequiredDownFails(t *testing.T) {
	s := NewServer(gin.TestMode)
	s.AddRequired(stubChecker{n: "postgres", err: errors.New("refused")})

	code, body := performHealth(t, s)
	if code != http.StatusServiceUnavailable {
		t.Fatalf("code = %d, want 503", code)
	}
	if body["status"] != "degraded" {
		t.Fatalf("status = %v, want degraded", body["status"])
	}
	comps := body["components"].(map[string]any)
	pg := comps["postgres"].(map[string]any)
	if pg["status"] != "down" {
		t.Fatalf("postgres = %v, want down", pg)
	}
}

func TestHealthOptionalDownStillOK(t *testing.T) {
	s := NewServer(gin.TestMode)
	s.AddRequired(stubChecker{n: "postgres"})
	s.AddOptional(stubChecker{n: "ai", err: errors.New("no local model endpoint")})

	code, body := performHealth(t, s)
	if code != http.StatusOK {
		t.Fatalf("code = %d, want 200 (optional dep down must not fail health)", code)
	}
	if body["status"] != "ok" {
		t.Fatalf("status = %v, want ok", body["status"])
	}
}

func TestPingRoute(t *testing.T) {
	s := NewServer(gin.TestMode)
	req := httptest.NewRequest(http.MethodGet, "/api/v1/ping", nil)
	w := httptest.NewRecorder()
	s.Router().ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("code = %d, want 200", w.Code)
	}
}
