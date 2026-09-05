// Package users owns the user table access.
package users

import (
	"context"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// User is the safe view of a user row (never carries the password hash).
type User struct {
	ID          string
	Email       string
	DisplayName string
	Role        string
	CreatedAt   time.Time
}

// Record is a full row including the password hash (internal use).
type Record struct {
	User
	PasswordHash string
}

var ErrNotFound = errors.New("user not found")

// Store reads and writes users in PostgreSQL.
type Store struct {
	pool *pgxpool.Pool
}

func NewStore(pool *pgxpool.Pool) *Store { return &Store{pool: pool} }

// Count returns the number of users (used for bootstrap detection).
func (s *Store) Count(ctx context.Context) (int, error) {
	var n int
	err := s.pool.QueryRow(ctx, "SELECT count(*) FROM users").Scan(&n)
	return n, err
}

// Create inserts a user with an already-hashed password.
func (s *Store) Create(ctx context.Context, email, passwordHash, displayName, role string) (User, error) {
	row := s.pool.QueryRow(ctx, `
		INSERT INTO users (email, password_hash, display_name, role)
		VALUES ($1, $2, $3, $4)
		RETURNING id, email, display_name, role, created_at`,
		email, passwordHash, displayName, role)
	return scanUser(row)
}

// ByEmail fetches a full user record by email.
func (s *Store) ByEmail(ctx context.Context, email string) (Record, error) {
	row := s.pool.QueryRow(ctx, `
		SELECT id, email, display_name, role, created_at, password_hash
		FROM users WHERE email = $1`, email)
	var r Record
	err := row.Scan(&r.ID, &r.Email, &r.DisplayName, &r.Role, &r.CreatedAt, &r.PasswordHash)
	if errors.Is(err, pgx.ErrNoRows) {
		return Record{}, ErrNotFound
	}
	if err != nil {
		return Record{}, err
	}
	return r, nil
}

func scanUser(row pgx.Row) (User, error) {
	var u User
	err := row.Scan(&u.ID, &u.Email, &u.DisplayName, &u.Role, &u.CreatedAt)
	if errors.Is(err, pgx.ErrNoRows) {
		return User{}, ErrNotFound
	}
	if err != nil {
		return User{}, err
	}
	return u, nil
}
