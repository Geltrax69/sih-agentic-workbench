package ask

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
)

// ModelsHandler lists the local models and switches the active chat model.
// Anyone signed in can see the list; only platform admins can switch, since
// the choice applies to every workspace.
type ModelsHandler struct {
	ai    *AIService
	audit *audit.Recorder
}

func NewModelsHandler(ai *AIService, auditRecorder *audit.Recorder) *ModelsHandler {
	return &ModelsHandler{ai: ai, audit: auditRecorder}
}

func (h *ModelsHandler) Register(protected *gin.RouterGroup) {
	protected.GET("/models", h.list)
	protected.POST("/models/active", h.setActive)
}

func (h *ModelsHandler) list(c *gin.Context) {
	var out map[string]any
	if err := h.ai.Get(c.Request.Context(), "/internal/models", &out); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": err.Error()})
		return
	}
	out["can_switch"] = auth.Role(c) == "admin"
	c.JSON(http.StatusOK, out)
}

type setActiveRequest struct {
	// Empty Model with Role "verifier" means "same as the answerer".
	Model string `json:"model" binding:"max=200"`
	Role  string `json:"role" binding:"omitempty,oneof=answerer verifier"`
}

func (h *ModelsHandler) setActive(c *gin.Context) {
	if auth.Role(c) != "admin" {
		c.JSON(http.StatusForbidden, gin.H{"error": "only admins can change the model"})
		return
	}
	var req setActiveRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid model or role"})
		return
	}
	var out map[string]any
	if err := h.ai.post(c.Request.Context(), "/internal/models/active", req, &out); err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": err.Error()})
		return
	}
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", "",
		"model.switched", "model", req.Model, map[string]any{"model": req.Model, "role": req.Role})
	c.JSON(http.StatusOK, out)
}
