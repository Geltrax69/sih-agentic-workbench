package ask

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
)

// MultiModelHandler exposes the multi-model pipeline over the protected API.
// Same trust model as ask: the workspace scope comes from the route param,
// the model list is a caller choice, never a permission.
type MultiModelHandler struct {
	ai    *AIService
	audit *audit.Recorder
}

func NewMultiModelHandler(ai *AIService, auditRecorder *audit.Recorder) *MultiModelHandler {
	return &MultiModelHandler{ai: ai, audit: auditRecorder}
}

func (h *MultiModelHandler) Register(protected *gin.RouterGroup, requireWsRole func(string) gin.HandlerFunc) {
	protected.POST("/workspaces/:wsId/ask/multi-model", requireWsRole("member"), h.ask)
}

type multiModelRequest struct {
	Question    string   `json:"question" binding:"required,min=1,max=4000"`
	Models      []string `json:"models" binding:"omitempty,max=6,dive,min=1,max=200"`
	Synthesizer string   `json:"synthesizer" binding:"omitempty,max=200"`
}

func (h *MultiModelHandler) ask(c *gin.Context) {
	var req multiModelRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "question is required; models max 6"})
		return
	}
	wsId := c.Param("wsId")
	var out map[string]any
	err := h.ai.post(c.Request.Context(), "/internal/query/multi-model", map[string]any{
		"workspace_id": wsId,
		"question":     req.Question,
		"models":       req.Models,
		"synthesizer":  req.Synthesizer,
	}, &out)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "ai service unavailable: " + err.Error()})
		return
	}
	modelsUsed, _ := out["models_used"].([]any)
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", wsId,
		"ask.multi_model_completed", "workspace", wsId,
		map[string]any{
			"models_used":    modelsUsed,
			"question_len":   len(req.Question),
			"synthesizer":    req.Synthesizer,
			"evidence_count": len(out["evidence"].([]any)),
		})
	c.JSON(http.StatusOK, out)
}
