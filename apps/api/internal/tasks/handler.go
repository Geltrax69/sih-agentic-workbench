// Package tasks exposes the agent task surface to the web client, proxying to
// the AI service orchestrator with the caller's identity attached.
package tasks

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/ask"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
)

type Handler struct {
	ai    *ask.AIService
	audit *audit.Recorder
}

func NewHandler(ai *ask.AIService, auditRecorder *audit.Recorder) *Handler {
	return &Handler{ai: ai, audit: auditRecorder}
}

func (h *Handler) Register(protected *gin.RouterGroup, requireWsRole func(string) gin.HandlerFunc) {
	protected.POST("/workspaces/:wsId/tasks", requireWsRole("member"), h.create)
	protected.GET("/tasks/:taskId", h.get)
	protected.POST("/tasks/:taskId/approval", h.decide)
}

type createRequest struct {
	Question string `json:"question" binding:"required,min=1,max=4000"`
}

type decisionRequest struct {
	Approved bool `json:"approved"`
}

func (h *Handler) create(c *gin.Context) {
	var req createRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "question is required"})
		return
	}
	var out map[string]any
	err := h.ai.Post(c.Request.Context(), "/internal/tasks", map[string]any{
		"workspace_id": c.Param("wsId"),
		"user_id":      auth.UserID(c),
		"question":     req.Question,
	}, &out)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, out)
}

func (h *Handler) get(c *gin.Context) {
	var out map[string]any
	if err := h.ai.Get(c.Request.Context(), "/internal/tasks/"+c.Param("taskId"), &out); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, out)
}

func (h *Handler) decide(c *gin.Context) {
	var req decisionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "body required"})
		return
	}
	var out map[string]any
	err := h.ai.Post(c.Request.Context(), "/internal/tasks/"+c.Param("taskId")+"/approval", map[string]any{
		"approved":   req.Approved,
		"decided_by": auth.UserID(c),
	}, &out)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", "",
		"task.approval.decided", "task", c.Param("taskId"), map[string]any{"approved": req.Approved})
	c.JSON(http.StatusOK, out)
}
