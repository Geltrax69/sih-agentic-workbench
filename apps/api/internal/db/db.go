// Package db owns the PostgreSQL connection pool and adapts it to migrate.Executor.
package db

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/migrate"
)

// Connect opens a pool and pings it, retrying briefly so the API can boot
// alongside a starting postgres container.
func Connect(ctx context.Context, url string) (*pgxpool.Pool, error) {
	cfg, err := pgxpool.ParseConfig(url)
	if err != nil {
		return nil, fmt.Errorf("parse DATABASE_URL: %w", err)
	}
	cfg.MaxConns = 10

	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		return nil, err
	}

	deadline := time.Now().Add(30 * time.Second)
	for {
		pingCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
		err = pool.Ping(pingCtx)
		cancel()
		if err == nil {
			return pool, nil
		}
		if time.Now().After(deadline) {
			pool.Close()
			return nil, fmt.Errorf("postgres not reachable: %w", err)
		}
		time.Sleep(500 * time.Millisecond)
	}
}

// Pool adapts *pgxpool.Pool to the migrate.Executor interface.
type Pool struct {
	*pgxpool.Pool
}

func (p Pool) Exec(ctx context.Context, sql string) error {
	_, err := p.Pool.Exec(ctx, sql)
	return err
}

func (p Pool) QueryString(ctx context.Context, sql string) (string, bool, error) {
	var name string
	err := p.Pool.QueryRow(ctx, sql).Scan(&name)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return "", false, nil
		}
		return "", false, err
	}
	return name, true, nil
}

var _ migrate.Executor = Pool{}
