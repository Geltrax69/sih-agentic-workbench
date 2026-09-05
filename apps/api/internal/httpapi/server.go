// Package httpapi defines the HTTP surface of the control-plane API.
package httpapi

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// Checker reports the health of one dependency.
type Checker interface {
	Name() string
	Check(ctx context.Context) error
}

// CheckerFunc adapts a function to Checker.
type CheckerFunc struct {
	N string
	F func(ctx context.Context) error
}

func (c CheckerFunc) Name() string                    { return c.N }
func (c CheckerFunc) Check(ctx context.Context) error { return c.F(ctx) }

// Required marks dependencies that make the service unhealthy when down.
// The AI service is intentionally optional at the health level: the workbench
// degrades (no reasoning) but stays manageable while the model endpoint is down.
type dependency struct {
	checker  Checker
	required bool
}

// Server holds the Gin router and registered dependencies.
type Server struct {
	deps []dependency
}

// NewServer builds the router. ginMode is gin.ReleaseMode or debug.
func NewServer(ginMode string) *Server {
	gin.SetMode(ginMode)
	return &Server{}
}

// AddRequired registers a dependency whose failure makes /healthz fail.
func (s *Server) AddRequired(c Checker) { s.deps = append(s.deps, dependency{c, true}) }

// AddOptional registers a dependency reported but non-fatal.
func (s *Server) AddOptional(c Checker) { s.deps = append(s.deps, dependency{c, false}) }

// Router assembles the routes.
func (s *Server) Router() *gin.Engine {
	r := gin.New()
	r.Use(gin.Recovery())

	r.GET("/healthz", s.health)
	r.GET("/api/v1/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})
	return r
}

func (s *Server) health(c *gin.Context) {
	ctx, cancel := context.WithTimeout(c.Request.Context(), 3*time.Second)
	defer cancel()

	components := gin.H{}
	healthy := true
	httpCode := http.StatusOK

	for _, d := range s.deps {
		err := d.checker.Check(ctx)
		if err != nil {
			components[d.checker.Name()] = gin.H{"status": "down", "error": err.Error()}
			if d.required {
				healthy = false
			}
		} else {
			components[d.checker.Name()] = gin.H{"status": "up"}
		}
	}

	if !healthy {
		httpCode = http.StatusServiceUnavailable
	}
	c.JSON(httpCode, gin.H{"status": statusWord(healthy), "components": components})
}

func statusWord(ok bool) string {
	if ok {
		return "ok"
	}
	return "degraded"
}
