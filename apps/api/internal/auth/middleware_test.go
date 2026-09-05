package auth

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
)

func newRouterWithProtected(secret string) (*gin.Engine, *gin.RouterGroup) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	protected := r.Group("/api/v1", Middleware(secret))
	protected.GET("/probe", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"user_id": UserID(c), "email": Email(c), "role": Role(c)})
	})
	return r, protected
}

func doRequest(r *gin.Engine, method, path, bearer string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, nil)
	if bearer != "" {
		req.Header.Set("Authorization", "Bearer "+bearer)
	}
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	return w
}

func TestMiddlewareValidTokenSetsContext(t *testing.T) {
	r, _ := newRouterWithProtected("secret-at-least-32-bytes-long!!")
	token, _ := IssueToken("secret-at-least-32-bytes-long!!", "u-1", "a@b.c", "admin", time.Hour)

	w := doRequest(r, http.MethodGet, "/api/v1/probe", token)
	if w.Code != http.StatusOK {
		t.Fatalf("code = %d, want 200 — %s", w.Code, w.Body.String())
	}
	var body map[string]string
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	want := map[string]string{"user_id": "u-1", "email": "a@b.c", "role": "admin"}
	for k, v := range want {
		if body[k] != v {
			t.Fatalf("body[%s] = %q, want %q", k, body[k], v)
		}
	}
}

func TestMiddlewareMissingToken401(t *testing.T) {
	r, _ := newRouterWithProtected("secret-at-least-32-bytes-long!!")
	if w := doRequest(r, http.MethodGet, "/api/v1/probe", ""); w.Code != http.StatusUnauthorized {
		t.Fatalf("code = %d, want 401", w.Code)
	}
}

func TestMiddlewareGarbageToken401(t *testing.T) {
	r, _ := newRouterWithProtected("secret-at-least-32-bytes-long!!")
	if w := doRequest(r, http.MethodGet, "/api/v1/probe", "not-a-jwt"); w.Code != http.StatusUnauthorized {
		t.Fatalf("code = %d, want 401", w.Code)
	}
}

func TestMiddlewareExpiredToken401(t *testing.T) {
	r, _ := newRouterWithProtected("secret-at-least-32-bytes-long!!")
	token, _ := IssueToken("secret-at-least-32-bytes-long!!", "u", "a@b.c", "member", -time.Minute)
	if w := doRequest(r, http.MethodGet, "/api/v1/probe", token); w.Code != http.StatusUnauthorized {
		t.Fatalf("code = %d, want 401", w.Code)
	}
}
