package workspaces

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
)

// Handler exposes the orgs/workspaces REST surface.
type Handler struct {
	store *Store
	audit *audit.Recorder
}

func NewHandler(store *Store, auditRecorder *audit.Recorder) *Handler {
	return &Handler{store: store, audit: auditRecorder}
}

type orgRequest struct {
	Name string `json:"name" binding:"required,min=1,max=200"`
}

type wsRequest struct {
	Name        string `json:"name" binding:"required,min=1,max=200"`
	Description string `json:"description" binding:"max=2000"`
}

type memberRequest struct {
	Email string `json:"email" binding:"required,email"`
	Role  string `json:"role" binding:"required"`
}

// Register mounts org/workspace routes. protected carries the auth middleware.
func (h *Handler) Register(protected *gin.RouterGroup) {
	protected.POST("/organizations", h.createOrg)
	protected.GET("/organizations", h.listMyOrgs)
	protected.POST("/organizations/:orgId/workspaces", h.requireOrgRole(RoleMember), h.createWorkspace)
	protected.GET("/organizations/:orgId/workspaces", h.requireOrgRole(RoleViewer), h.listOrgWorkspaces)
	protected.GET("/workspaces", h.listMyWorkspaces)
	protected.GET("/workspaces/:wsId/members", h.requireWsRole(RoleViewer), h.listMembers)
	protected.POST("/workspaces/:wsId/members", h.requireWsRole(RoleWorkspaceOwner), h.addMember)
}

// requireOrgRole authorizes by :orgId. Denials are audited.
func (h *Handler) requireOrgRole(minRole string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID := auth.UserID(c)
		role, err := h.store.OrgRole(c.Request.Context(), c.Param("orgId"), userID)
		if err != nil || !RoleAtLeast(role, minRole) {
			h.audit.Event(c.Request.Context(), userID, "", c.Param("orgId"), "workspace.access.denied", "organization", c.Param("orgId"), map[string]any{"need": minRole})
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "forbidden"})
			return
		}
		c.Set("org_role", role)
		c.Next()
	}
}

// requireWsRole authorizes by :wsId. Denials are audited.
func (h *Handler) requireWsRole(minRole string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID := auth.UserID(c)
		role, err := h.store.WorkspaceRole(c.Request.Context(), c.Param("wsId"), userID)
		if err != nil || !RoleAtLeast(role, minRole) {
			h.audit.Event(c.Request.Context(), userID, "", c.Param("wsId"), "workspace.access.denied", "workspace", c.Param("wsId"), map[string]any{"need": minRole})
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "forbidden"})
			return
		}
		c.Set("ws_role", role)
		c.Next()
	}
}

func (h *Handler) createOrg(c *gin.Context) {
	var req orgRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "name is required"})
		return
	}
	org, err := h.store.CreateOrganization(c.Request.Context(), req.Name, auth.UserID(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "could not create organization"})
		return
	}
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", "", "org.created", "organization", org.ID, nil)
	c.JSON(http.StatusCreated, org)
}

func (h *Handler) listMyOrgs(c *gin.Context) {
	orgs, err := h.store.OrganizationsFor(c.Request.Context(), auth.UserID(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failed"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"organizations": orgs})
}

func (h *Handler) createWorkspace(c *gin.Context) {
	var req wsRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "name is required"})
		return
	}
	ws, err := h.store.CreateWorkspace(c.Request.Context(), c.Param("orgId"), req.Name, req.Description, auth.UserID(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "could not create workspace"})
		return
	}
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", ws.ID, "workspace.created", "workspace", ws.ID, nil)
	c.JSON(http.StatusCreated, ws)
}

func (h *Handler) listOrgWorkspaces(c *gin.Context) {
	ws, err := h.store.WorkspacesInOrg(c.Request.Context(), c.Param("orgId"))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failed"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"workspaces": ws})
}

func (h *Handler) listMyWorkspaces(c *gin.Context) {
	ws, err := h.store.WorkspacesFor(c.Request.Context(), auth.UserID(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failed"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"workspaces": ws})
}

func (h *Handler) listMembers(c *gin.Context) {
	members, err := h.store.Members(c.Request.Context(), c.Param("wsId"))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failed"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"members": members})
}

func (h *Handler) addMember(c *gin.Context) {
	var req memberRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "email and role are required"})
		return
	}
	err := h.store.AddMember(c.Request.Context(), c.Param("wsId"), req.Email, req.Role)
	if errors.Is(err, ErrNotFound) {
		c.JSON(http.StatusNotFound, gin.H{"error": "no such user"})
		return
	}
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid role"})
		return
	}
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", c.Param("wsId"), "workspace.member.added", "workspace", c.Param("wsId"), map[string]any{"email": req.Email, "role": req.Role})
	c.JSON(http.StatusOK, gin.H{"status": "added"})
}
