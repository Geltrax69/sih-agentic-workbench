package documents

import (
	"bytes"
	"io"
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/auth"
)

// Handler exposes document routes on protected groups.
type Handler struct {
	store   *Store
	storage Storage
	audit   *audit.Recorder
}

func NewHandler(store *Store, storage Storage, auditRecorder *audit.Recorder) *Handler {
	return &Handler{store: store, storage: storage, audit: auditRecorder}
}

// Register mounts document routes. requireWsRole is the workspace-role
// middleware provided by the workspaces package (shared :wsId param).
func (h *Handler) Register(protected *gin.RouterGroup, requireWsRole func(string) gin.HandlerFunc) {
	protected.POST("/workspaces/:wsId/documents", requireWsRole("member"), h.upload)
	protected.GET("/workspaces/:wsId/documents", requireWsRole("viewer"), h.list)
	protected.GET("/documents/:docId", requireWsRole("viewer"), h.byID)
	protected.DELETE("/documents/:docId", requireWsRole("workspace_owner"), h.delete)
}

func (h *Handler) upload(c *gin.Context) {
	fh, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "multipart field 'file' is required"})
		return
	}
	if fh.Size > MaxUploadBytes {
		c.JSON(http.StatusRequestEntityTooLarge, gin.H{"error": "file exceeds 50MB limit"})
		return
	}
	contentType := fh.Header.Get("Content-Type")
	if _, ok := AllowedContentTypes[contentType]; !ok {
		h.audit.Event(c.Request.Context(), auth.UserID(c), "", c.Param("wsId"),
			"document.upload.rejected", "document", fh.Filename, map[string]any{"mime": contentType})
		c.JSON(http.StatusUnsupportedMediaType, gin.H{"error": "unsupported file type: " + contentType})
		return
	}
	src, err := fh.Open()
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "cannot read upload"})
		return
	}
	defer src.Close()

	// read into memory with a hard cap: guards bombs and makes size
	// authoritative regardless of client headers.
	data, err := io.ReadAll(io.LimitReader(src, MaxUploadBytes+1))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "cannot read upload"})
		return
	}
	if int64(len(data)) > MaxUploadBytes {
		c.JSON(http.StatusRequestEntityTooLarge, gin.H{"error": "file exceeds 50MB limit"})
		return
	}

	doc, err := h.store.Create(c.Request.Context(), c.Param("wsId"), auth.UserID(c),
		fh.Filename, contentType, int64(len(data)), bytes.NewReader(data), h.storage)
	if err != nil {
		if err == ErrTooLarge {
			c.JSON(http.StatusRequestEntityTooLarge, gin.H{"error": "file exceeds 50MB limit"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "upload failed"})
		return
	}
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", c.Param("wsId"),
		"document.uploaded", "document", doc.ID, map[string]any{"filename": doc.Filename, "size": doc.SizeBytes})
	c.JSON(http.StatusCreated, doc)
}

func (h *Handler) list(c *gin.Context) {
	docs, err := h.store.List(c.Request.Context(), c.Param("wsId"))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failed"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"documents": docs})
}

func (h *Handler) byID(c *gin.Context) {
	doc, err := h.store.ByID(c.Request.Context(), c.Param("docId"))
	if err == ErrNotFound {
		c.JSON(http.StatusNotFound, gin.H{"error": "not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failed"})
		return
	}
	c.JSON(http.StatusOK, doc)
}

func (h *Handler) delete(c *gin.Context) {
	doc, err := h.store.ByID(c.Request.Context(), c.Param("docId"))
	if err == ErrNotFound {
		c.JSON(http.StatusNotFound, gin.H{"error": "not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failed"})
		return
	}
	if err := h.store.Delete(c.Request.Context(), doc.ID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "delete failed"})
		return
	}
	h.audit.Event(c.Request.Context(), auth.UserID(c), "", doc.WorkspaceID,
		"document.deleted", "document", doc.ID, map[string]any{"filename": doc.Filename})
	c.JSON(http.StatusOK, gin.H{"status": "deleted"})
}
