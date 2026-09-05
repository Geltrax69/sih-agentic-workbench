package auth

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

const (
	// Context keys set by Middleware after successful token validation.
	CtxUserID = "auth_user_id"
	CtxEmail  = "auth_email"
	CtxRole   = "auth_role"
)

// Middleware authenticates requests via the Authorization: Bearer header.
// On success it stores the claims in the gin context; otherwise it aborts
// with a generic 401.
func Middleware(secret string) gin.HandlerFunc {
	return func(c *gin.Context) {
		header := c.GetHeader("Authorization")
		token, ok := strings.CutPrefix(header, "Bearer ")
		if !ok || strings.TrimSpace(token) == "" {
			abortUnauthorized(c, "missing bearer token")
			return
		}
		claims, err := ParseToken(secret, token)
		if err != nil {
			abortUnauthorized(c, "invalid or expired token")
			return
		}
		c.Set(CtxUserID, claims.UserID)
		c.Set(CtxEmail, claims.Email)
		c.Set(CtxRole, claims.Role)
		c.Next()
	}
}

func abortUnauthorized(c *gin.Context, _ string) {
	// Body stays generic: never reveal why authentication failed.
	c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "authentication required"})
}

// UserID returns the authenticated user's ID from the request context.
func UserID(c *gin.Context) string {
	v, _ := c.Get(CtxUserID)
	s, _ := v.(string)
	return s
}

// Email returns the authenticated user's email from the request context.
func Email(c *gin.Context) string {
	v, _ := c.Get(CtxEmail)
	s, _ := v.(string)
	return s
}

// Role returns the authenticated user's role from the request context.
func Role(c *gin.Context) string {
	v, _ := c.Get(CtxRole)
	s, _ := v.(string)
	return s
}
