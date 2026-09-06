// Package ask forwards grounded questions to the AI service with the caller's
// workspace scope. The AI service receives the scope; it never derives it.
package ask

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
)

// AIService is the internal HTTP surface of the Python AI service.
type AIService struct {
	BaseURL        string
	InternalSecret string
	Client         *http.Client
}

func NewAIService(baseURL, secret string) *AIService {
	return &AIService{
		BaseURL:        baseURL,
		InternalSecret: secret,
		Client:         &http.Client{Timeout: 180 * time.Second},
	}
}

func (a *AIService) post(ctx context.Context, path string, payload any, out any) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, a.BaseURL+path, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Internal-Secret", a.InternalSecret)
	resp, err := a.Client.Do(req)
	if err != nil {
		return fmt.Errorf("ai service unreachable: %w", err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("ai service %s: HTTP %d: %s", path, resp.StatusCode, truncate(raw, 200))
	}
	return json.Unmarshal(raw, out)
}

// TriggerIngestion asks the AI service to process pending ingestion jobs.
// Non-blocking errors are returned for logging only.
func (a *AIService) TriggerIngestion(ctx context.Context) error {
	return a.post(ctx, "/internal/ingest/run", map[string]any{}, &map[string]any{})
}

type Evidence struct {
	ChunkID    string  `json:"chunk_id"`
	DocumentID string  `json:"document_id"`
	Filename   string  `json:"filename"`
	ChunkIndex int     `json:"chunk_index"`
	Content    string  `json:"content"`
	Score      float64 `json:"score"`
}

type AskResponse struct {
	Answer   string     `json:"answer"`
	Evidence []Evidence `json:"evidence"`
}

// Handler exposes POST /workspaces/:wsId/ask on the protected group.
type Handler struct {
	ai    *AIService
	audit *audit.Recorder
}

func NewHandler(ai *AIService, auditRecorder *audit.Recorder) *Handler {
	return &Handler{ai: ai, audit: auditRecorder}
}

func (h *Handler) Register(protected *gin.RouterGroup, requireWsRole func(string) gin.HandlerFunc) {
	protected.POST("/workspaces/:wsId/ask", requireWsRole("member"), h.ask)
}

type askRequest struct {
	Question string `json:"question" binding:"required,min=1,max=4000"`
}

func (h *Handler) ask(c *gin.Context) {
	var req askRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "question is required"})
		return
	}
	var out AskResponse
	err := h.ai.post(c.Request.Context(), "/internal/query", map[string]any{
		"workspace_id": c.Param("wsId"),
		"question":     req.Question,
	}, &out)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "ai service unavailable: " + err.Error()})
		return
	}
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", c.Param("wsId"),
		"ask.completed", "workspace", c.Param("wsId"),
		map[string]any{"evidence_count": len(out.Evidence)})
	c.JSON(http.StatusOK, out)
}

func truncate(b []byte, n int) string {
	if len(b) <= n {
		return string(b)
	}
	return string(b[:n]) + "..."
}
