package auth

import (
	"errors"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

type loginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=1"`
}

type loginResponse struct {
	Token string      `json:"token"`
	User  userPayload `json:"user"`
}

type userPayload struct {
	ID          string `json:"id"`
	Email       string `json:"email"`
	DisplayName string `json:"display_name"`
	Role        string `json:"role"`
}

// RegisterRoutes mounts the public login route and the /auth/me probe inside
// the protected group. Protected carries the auth middleware and is where all
// future feature packages add their routes.
func RegisterRoutes(public, protected *gin.RouterGroup, svc *Service) {
	public.POST("/auth/login", svc.handleLogin)
	protected.GET("/auth/me", svc.handleMe)
}

func (s *Service) handleLogin(c *gin.Context) {
	var req loginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "email and password are required"})
		return
	}
	req.Email = strings.ToLower(strings.TrimSpace(req.Email))

	result, err := s.Login(c.Request.Context(), req.Email, req.Password)
	if err != nil {
		if errors.Is(err, ErrInvalidCredentials) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid email or password"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "login failed"})
		return
	}

	c.JSON(http.StatusOK, loginResponse{
		Token: result.Token,
		User: userPayload{
			ID:          result.User.ID,
			Email:       result.User.Email,
			DisplayName: result.User.DisplayName,
			Role:        result.User.Role,
		},
	})
}

func (s *Service) handleMe(c *gin.Context) {
	id := UserID(c)
	if id == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "authentication required"})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"id":    id,
		"email": Email(c),
		"role":  Role(c),
	})
}
