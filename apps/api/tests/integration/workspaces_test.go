//go:build integration

package integration

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/db"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/migrate"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/users"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/workspaces"
)

// wsTestEnv wires a full router (auth + workspaces) against the live DB.
func wsTestEnv(t *testing.T) (*gin.Engine, *users.Store) {
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
	wsStore := workspaces.NewStore(pool)

	gin.SetMode(gin.TestMode)
	r := gin.New()
	public := r.Group("/api/v1")
	protected := r.Group("/api/v1", auth.Middleware(testSecret))
	auth.RegisterRoutes(public, protected, svc)
	workspaces.NewHandler(wsStore, recorder).Register(protected)
	return r, store
}

type testUser struct {
	id    string
	email string
	token string
}

type wsInfo struct {
	ID    string
	OrgID string
}

type httpResp struct {
	code int
	body string
}

func doReq(r *gin.Engine, method, path, token string, body []byte) httpResp {
	var reader *strings.Reader
	if body != nil {
		reader = strings.NewReader(string(body))
	} else {
		reader = strings.NewReader("")
	}
	req := httptest.NewRequest(method, path, reader)
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	return httpResp{code: w.Code, body: w.Body.String()}
}

func (h httpResp) json(t *testing.T, into any) {
	t.Helper()
	if err := json.Unmarshal([]byte(h.body), into); err != nil {
		t.Fatalf("invalid JSON %q: %v", h.body, err)
	}
}

// createTestUser inserts a user directly and logs in via the API.
func createTestUser(t *testing.T, r *gin.Engine, store *users.Store, email, password, role string) testUser {
	t.Helper()
	hash, err := auth.HashPassword(password)
	if err != nil {
		t.Fatal(err)
	}
	u, err := store.Create(context.Background(), email, hash, "IT "+email, role)
	if err != nil {
		t.Fatalf("seed user: %v", err)
	}
	w := doReq(r, http.MethodPost, "/api/v1/auth/login", "", []byte(fmt.Sprintf(`{"email":%q,"password":%q}`, email, password)))
	if w.code != http.StatusOK {
		t.Fatalf("login failed: %d %s", w.code, w.body)
	}
	var lr struct {
		Token string `json:"token"`
	}
	w.json(t, &lr)
	return testUser{id: u.ID, email: email, token: lr.Token}
}

// createOrgWorkspace creates an org and a workspace inside it via the API.
func createOrgWorkspace(t *testing.T, r *gin.Engine, u testUser, orgName, wsName string) wsInfo {
	t.Helper()
	w := doReq(r, http.MethodPost, "/api/v1/organizations", u.token,
		[]byte(fmt.Sprintf(`{"name":%q}`, orgName)))
	if w.code != http.StatusCreated {
		t.Fatalf("create org: %d %s", w.code, w.body)
	}
	var org struct {
		ID string `json:"id"`
	}
	w.json(t, &org)

	w = doReq(r, http.MethodPost, "/api/v1/organizations/"+org.ID+"/workspaces", u.token,
		[]byte(fmt.Sprintf(`{"name":%q,"description":"it"}`, wsName)))
	if w.code != http.StatusCreated {
		t.Fatalf("create workspace: %d %s", w.code, w.body)
	}
	var ws struct {
		ID string `json:"id"`
	}
	w.json(t, &ws)
	return wsInfo{ID: ws.ID, OrgID: org.ID}
}

func uniqEmailP1() string {
	return fmt.Sprintf("ws-it-%d@test.local", time.Now().UnixNano())
}

func countAudit(t *testing.T, eventType, userID string) int {
	t.Helper()
	p := poolFromEnv(t)
	var n int
	if err := p.QueryRow(context.Background(),
		"SELECT count(*) FROM audit_events WHERE event_type = $1 AND user_id = $2",
		eventType, userID).Scan(&n); err != nil {
		t.Fatalf("audit count: %v", err)
	}
	return n
}

func TestWorkspaceIsolation(t *testing.T) {
	r, store := wsTestEnv(t)

	// A and B each get their own org + workspace
	userA := createTestUser(t, r, store, uniqEmailP1(), "Passw0rdA!long", "member")
	wsA := createOrgWorkspace(t, r, userA, "Org A", "WS A")
	userB := createTestUser(t, r, store, uniqEmailP1(), "Passw0rdB!long", "member")
	_ = createOrgWorkspace(t, r, userB, "Org B", "WS B")

	t.Run("owner creates and lists own workspace", func(t *testing.T) {
		w := doReq(r, http.MethodGet, "/api/v1/workspaces", userA.token, nil)
		if w.code != http.StatusOK {
			t.Fatalf("code = %d, body = %s", w.code, w.body)
		}
		if !strings.Contains(w.body, wsA.ID) {
			t.Fatalf("own workspace missing from list: %s", w.body)
		}
	})

	t.Run("cross-workspace members denied 403", func(t *testing.T) {
		w := doReq(r, http.MethodGet, "/api/v1/workspaces/"+wsA.ID+"/members", userB.token, nil)
		if w.code != http.StatusForbidden {
			t.Fatalf("cross-workspace members: code = %d, want 403", w.code)
		}
	})

	t.Run("cross-org workspaces denied 403", func(t *testing.T) {
		w := doReq(r, http.MethodGet, "/api/v1/organizations/"+wsA.OrgID+"/workspaces", userB.token, nil)
		if w.code != http.StatusForbidden {
			t.Fatalf("cross-org workspaces: code = %d, want 403", w.code)
		}
	})

	t.Run("no auth on protected routes", func(t *testing.T) {
		w := doReq(r, http.MethodGet, "/api/v1/workspaces", "", nil)
		if w.code != http.StatusUnauthorized {
			t.Fatalf("code = %d, want 401", w.code)
		}
	})

	t.Run("workspace owner adds member who can then view", func(t *testing.T) {
		userC := createTestUser(t, r, store, uniqEmailP1(), "Passw0rdC!long", "member")
		w := doReq(r, http.MethodPost, "/api/v1/workspaces/"+wsA.ID+"/members", userA.token,
			[]byte(fmt.Sprintf(`{"email":%q,"role":"viewer"}`, userC.email)))
		if w.code != http.StatusOK {
			t.Fatalf("add member: %d %s", w.code, w.body)
		}
		// now C (viewer) can list members but B still cannot
		w = doReq(r, http.MethodGet, "/api/v1/workspaces/"+wsA.ID+"/members", userC.token, nil)
		if w.code != http.StatusOK {
			t.Fatalf("new viewer member list: %d %s", w.code, w.body)
		}
		w = doReq(r, http.MethodGet, "/api/v1/workspaces/"+wsA.ID+"/members", userB.token, nil)
		if w.code != http.StatusForbidden {
			t.Fatalf("B must still be denied: %d", w.code)
		}
	})

	t.Run("denials audited", func(t *testing.T) {
		if n := countAudit(t, "workspace.access.denied", userB.id); n < 3 {
			t.Fatalf("expected >=3 denial events for user B, got %d", n)
		}
	})
}
