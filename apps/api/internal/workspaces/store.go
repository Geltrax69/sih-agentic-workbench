// Package workspaces implements organizations, workspaces and memberships.
// Authorization is resolved here (Go) and passed downstream — see ADR-002.
package workspaces

import (
	"context"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Role hierarchy for memberships. Higher value = more capability.
const (
	RoleViewer         = "viewer"
	RoleMember         = "member"
	RoleWorkspaceOwner = "workspace_owner"
	RoleOrgOwner       = "org_owner"
	RoleAdmin          = "admin" // global admin
)

// RoleLevel maps a role to its rank for comparisons. -1 = unknown.
func RoleLevel(role string) int {
	switch role {
	case RoleAdmin:
		return 100
	case RoleOrgOwner:
		return 40
	case RoleWorkspaceOwner:
		return 30
	case RoleMember:
		return 20
	case RoleViewer:
		return 10
	default:
		return -1
	}
}

// RoleAtLeast reports whether have satisfies want.
func RoleAtLeast(have, want string) bool {
	return RoleLevel(have) >= RoleLevel(want)
}

var (
	ErrNotFound = errors.New("not found")
	ErrConflict = errors.New("already exists")
)

type Organization struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	CreatedBy string    `json:"created_by"`
	CreatedAt time.Time `json:"created_at"`
}

type Workspace struct {
	ID             string    `json:"id"`
	OrganizationID string    `json:"organization_id"`
	Name           string    `json:"name"`
	Description    string    `json:"description"`
	CreatedAt      time.Time `json:"created_at"`
}

// Store owns all membership queries. Every query is scoped by user where
// authorization demands it — a caller can only ever touch what it passes.
type Store struct {
	pool *pgxpool.Pool
}

func NewStore(pool *pgxpool.Pool) *Store { return &Store{pool: pool} }

// --- organizations ---

func (s *Store) CreateOrganization(ctx context.Context, name, createdBy string) (Organization, error) {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return Organization{}, err
	}
	defer tx.Rollback(ctx)

	var org Organization
	err = tx.QueryRow(ctx,
		`INSERT INTO organizations (name, created_by) VALUES ($1, $2)
		 RETURNING id, name, created_by, created_at`, name, createdBy).
		Scan(&org.ID, &org.Name, &org.CreatedBy, &org.CreatedAt)
	if err != nil {
		return Organization{}, err
	}
	if _, err := tx.Exec(ctx,
		`INSERT INTO organization_members (organization_id, user_id, role) VALUES ($1, $2, $3)`,
		org.ID, createdBy, RoleOrgOwner); err != nil {
		return Organization{}, err
	}
	if err := tx.Commit(ctx); err != nil {
		return Organization{}, err
	}
	return org, nil
}

// OrganizationsFor lists orgs the user belongs to.
func (s *Store) OrganizationsFor(ctx context.Context, userID string) ([]Organization, error) {
	rows, err := s.pool.Query(ctx, `
		SELECT o.id, o.name, o.created_by, o.created_at
		FROM organizations o
		JOIN organization_members m ON m.organization_id = o.id
		WHERE m.user_id = $1 ORDER BY o.created_at`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Organization
	for rows.Next() {
		var o Organization
		if err := rows.Scan(&o.ID, &o.Name, &o.CreatedBy, &o.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, o)
	}
	return out, rows.Err()
}

// OrgRole returns the user's role in the org ("" if not a member).
func (s *Store) OrgRole(ctx context.Context, orgID, userID string) (string, error) {
	var role string
	err := s.pool.QueryRow(ctx,
		`SELECT role FROM organization_members WHERE organization_id = $1 AND user_id = $2`,
		orgID, userID).Scan(&role)
	if errors.Is(err, pgx.ErrNoRows) {
		// global admins act as org owners
		var globalRole string
		if err2 := s.pool.QueryRow(ctx, `SELECT role FROM users WHERE id = $1`, userID).Scan(&globalRole); err2 == nil && globalRole == RoleAdmin {
			return RoleOrgOwner, nil
		}
		return "", nil
	}
	return role, err
}

// --- workspaces ---

func (s *Store) CreateWorkspace(ctx context.Context, orgID, name, description, createdBy string) (Workspace, error) {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return Workspace{}, err
	}
	defer tx.Rollback(ctx)

	var ws Workspace
	err = tx.QueryRow(ctx,
		`INSERT INTO workspaces (organization_id, name, description, created_by) VALUES ($1, $2, $3, $4)
		 RETURNING id, organization_id, name, description, created_at`,
		orgID, name, description, createdBy).
		Scan(&ws.ID, &ws.OrganizationID, &ws.Name, &ws.Description, &ws.CreatedAt)
	if err != nil {
		return Workspace{}, err
	}
	if _, err := tx.Exec(ctx,
		`INSERT INTO workspace_members (workspace_id, user_id, role) VALUES ($1, $2, $3)`,
		ws.ID, createdBy, RoleWorkspaceOwner); err != nil {
		return Workspace{}, err
	}
	if err := tx.Commit(ctx); err != nil {
		return Workspace{}, err
	}
	return ws, nil
}

// WorkspacesInOrg lists workspaces of one org the user can see (member of the
// org sees all its workspaces).
func (s *Store) WorkspacesInOrg(ctx context.Context, orgID string) ([]Workspace, error) {
	rows, err := s.pool.Query(ctx, `
		SELECT id, organization_id, name, COALESCE(description,''), created_at
		FROM workspaces WHERE organization_id = $1 ORDER BY created_at`, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanWorkspaces(rows)
}

// WorkspacesFor lists workspaces the user is a member of.
func (s *Store) WorkspacesFor(ctx context.Context, userID string) ([]Workspace, error) {
	rows, err := s.pool.Query(ctx, `
		SELECT w.id, w.organization_id, w.name, COALESCE(w.description,''), w.created_at
		FROM workspaces w
		JOIN workspace_members m ON m.workspace_id = w.id
		WHERE m.user_id = $1 ORDER BY w.created_at`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanWorkspaces(rows)
}

// WorkspaceRole returns the user's role in the workspace ("" if none).
func (s *Store) WorkspaceRole(ctx context.Context, workspaceID, userID string) (string, error) {
	var role string
	err := s.pool.QueryRow(ctx,
		`SELECT role FROM workspace_members WHERE workspace_id = $1 AND user_id = $2`,
		workspaceID, userID).Scan(&role)
	if errors.Is(err, pgx.ErrNoRows) {
		// org owners and global admins inherit workspace_owner
		orgRole, err := s.OrgRoleByWorkspace(ctx, workspaceID, userID)
		if err != nil || orgRole == "" {
			return "", nil
		}
		return RoleWorkspaceOwner, nil
	}
	if err != nil {
		return "", err
	}
	return role, nil
}

// OrgRoleByWorkspace resolves the user's org role through a workspace.
func (s *Store) OrgRoleByWorkspace(ctx context.Context, workspaceID, userID string) (string, error) {
	var role string
	err := s.pool.QueryRow(ctx, `
		SELECT m.role FROM organization_members m
		JOIN workspaces w ON w.organization_id = m.organization_id
		WHERE w.id = $1 AND m.user_id = $2`, workspaceID, userID).Scan(&role)
	if errors.Is(err, pgx.ErrNoRows) {
		return "", nil
	}
	return role, err
}

// AddMember adds a user to a workspace (email-keyed). ErrNotFound if no user.
func (s *Store) AddMember(ctx context.Context, workspaceID, email, role string) error {
	if RoleLevel(role) < RoleLevel(RoleViewer) || RoleLevel(role) > RoleLevel(RoleWorkspaceOwner) {
		return errors.New("invalid workspace role")
	}
	tag, err := s.pool.Exec(ctx, `
		INSERT INTO workspace_members (workspace_id, user_id, role)
		SELECT $1, id, $2 FROM users WHERE email = $3
		ON CONFLICT (workspace_id, user_id) DO UPDATE SET role = EXCLUDED.role`,
		workspaceID, role, email)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNotFound
	}
	return nil
}

type Member struct {
	UserID      string
	Email       string
	DisplayName string
	Role        string
}

func (s *Store) Members(ctx context.Context, workspaceID string) ([]Member, error) {
	rows, err := s.pool.Query(ctx, `
		SELECT u.id, u.email, u.display_name, m.role
		FROM workspace_members m JOIN users u ON u.id = m.user_id
		WHERE m.workspace_id = $1 ORDER BY m.created_at`, workspaceID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Member
	for rows.Next() {
		var m Member
		if err := rows.Scan(&m.UserID, &m.Email, &m.DisplayName, &m.Role); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}

// WorkspaceOrg returns the org id of a workspace.
func (s *Store) WorkspaceOrg(ctx context.Context, workspaceID string) (string, error) {
	var orgID string
	err := s.pool.QueryRow(ctx, `SELECT organization_id FROM workspaces WHERE id = $1`, workspaceID).Scan(&orgID)
	if errors.Is(err, pgx.ErrNoRows) {
		return "", ErrNotFound
	}
	return orgID, err
}

func scanWorkspaces(rows pgx.Rows) ([]Workspace, error) {
	var out []Workspace
	for rows.Next() {
		var w Workspace
		if err := rows.Scan(&w.ID, &w.OrganizationID, &w.Name, &w.Description, &w.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, w)
	}
	return out, rows.Err()
}
