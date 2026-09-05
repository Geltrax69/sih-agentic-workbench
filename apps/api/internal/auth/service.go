package auth

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/audit"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/users"
)

// ErrInvalidCredentials is returned for any login failure where the account
// may or may not exist. Handlers must map it to a generic 401.
var ErrInvalidCredentials = errors.New("invalid credentials")

// LoginResult carries a fresh session token and the authenticated user.
type LoginResult struct {
	Token string
	User  users.User
}

// Service authenticates users against the store and issues JWT sessions.
type Service struct {
	store  *users.Store
	audit  *audit.Recorder
	secret string
	ttl    time.Duration
}

func NewService(store *users.Store, auditRecorder *audit.Recorder, secret string, ttl time.Duration) *Service {
	return &Service{store: store, audit: auditRecorder, secret: secret, ttl: ttl}
}

// Login verifies credentials and returns a signed token. Unknown email and
// wrong password are indistinguishable to the caller (and in the audit log
// reason), but both are audited.
func (s *Service) Login(ctx context.Context, email, password string) (LoginResult, error) {
	rec, err := s.store.ByEmail(ctx, email)
	if errors.Is(err, users.ErrNotFound) {
		_ = VerifyPassword(dummyHash, password) // equalize timing
		s.audit.Event(ctx, "", "", "", "auth.login.failure", "user", email, map[string]any{"reason": "unknown_email"})
		return LoginResult{}, ErrInvalidCredentials
	}
	if err != nil {
		return LoginResult{}, fmt.Errorf("login: %w", err)
	}

	if !VerifyPassword(rec.PasswordHash, password) {
		s.audit.Event(ctx, rec.ID, "", "", "auth.login.failure", "user", rec.Email, map[string]any{"reason": "bad_password"})
		return LoginResult{}, ErrInvalidCredentials
	}

	token, err := IssueToken(s.secret, rec.ID, rec.Email, rec.Role, s.ttl)
	if err != nil {
		return LoginResult{}, fmt.Errorf("login: %w", err)
	}

	s.audit.Event(ctx, rec.ID, "", "", "auth.login.success", "user", rec.Email, nil)
	return LoginResult{Token: token, User: rec.User}, nil
}

// BootstrapAdmin creates the initial admin when the users table is empty.
// It is a no-op when users already exist or when no bootstrap password is
// configured. Returns whether a user was created.
func (s *Service) BootstrapAdmin(ctx context.Context, email, password, displayName string) (bool, error) {
	if password == "" {
		return false, nil
	}
	n, err := s.store.Count(ctx)
	if err != nil {
		return false, fmt.Errorf("bootstrap check: %w", err)
	}
	if n > 0 {
		return false, nil
	}
	hash, err := HashPassword(password)
	if err != nil {
		return false, fmt.Errorf("bootstrap admin: %w", err)
	}
	u, err := s.store.Create(ctx, email, hash, displayName, "admin")
	if err != nil {
		return false, fmt.Errorf("bootstrap admin: %w", err)
	}
	s.audit.Event(ctx, u.ID, "", "", "auth.bootstrap.admin_created", "user", u.Email, nil)
	return true, nil
}
