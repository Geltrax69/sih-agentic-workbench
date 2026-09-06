// Package documents owns document upload, storage metadata and lifecycle.
package documents

import (
	"context"
	"errors"
	"fmt"
	"io"
	"path"
	"regexp"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/minio/minio-go/v7"
)

const MaxUploadBytes = 50 << 20 // 50 MB

// AllowedContentTypes maps accepted MIME types to canonical extensions.
var AllowedContentTypes = map[string]string{
	"application/pdf": ".pdf",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
	"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":       ".xlsx",
	"text/plain":      ".txt",
	"text/markdown":   ".md",
	"text/csv":        ".csv",
	"application/csv": ".csv",
	"image/jpeg":      ".jpg",
	"image/png":       ".png",
}

var ErrUnsupportedType = errors.New("unsupported file type")
var ErrTooLarge = errors.New("file too large")
var ErrNotFound = errors.New("document not found")

type Document struct {
	ID          string    `json:"id"`
	WorkspaceID string    `json:"workspace_id"`
	Filename    string    `json:"filename"`
	MimeType    string    `json:"mime_type"`
	SizeBytes   int64     `json:"size_bytes"`
	Status      string    `json:"status"`
	CreatedAt   time.Time `json:"created_at"`
}

// Statuses: UPLOADED | PROCESSING | INDEXED | FAILED | QUARANTINED
const (
	StatusUploaded    = "UPLOADED"
	StatusProcessing  = "PROCESSING"
	StatusIndexed     = "INDEXED"
	StatusFailed      = "FAILED"
	StatusQuarantined = "QUARANTINED"
)

// Storage is the object-store surface (MinIO).
type Storage interface {
	PutObject(ctx context.Context, key string, r io.Reader, size int64, contentType string) error
}

// MinioStorage adapts the minio client.
type MinioStorage struct {
	Client *minio.Client
	Bucket string
}

func (m *MinioStorage) PutObject(ctx context.Context, key string, r io.Reader, size int64, contentType string) error {
	_, err := m.Client.PutObject(ctx, m.Bucket, key, r, size, minio.PutObjectOptions{ContentType: contentType})
	return err
}

// EnsureBucket creates the bucket if missing.
func (m *MinioStorage) EnsureBucket(ctx context.Context) error {
	exists, err := m.Client.BucketExists(ctx, m.Bucket)
	if err != nil {
		return err
	}
	if !exists {
		return m.Client.MakeBucket(ctx, m.Bucket, minio.MakeBucketOptions{})
	}
	return nil
}

// Store owns document rows + ingestion jobs.
type Store struct {
	pool *pgxpool.Pool
}

func NewStore(pool *pgxpool.Pool) *Store { return &Store{pool: pool} }

// ObjectKey builds the UUID-based storage key (never user-controlled paths).
func ObjectKey(docID, ext string) string {
	return path.Join("documents", docID+ext)
}

// Create stores metadata + the raw object and opens an ingestion job.
// size <= 0 means unknown (streamed); the limit is still enforced by the caller.
func (s *Store) Create(ctx context.Context, wsID, uploadedBy, filename, mimeType string, size int64, content io.Reader, storage Storage) (Document, error) {
	ext, ok := AllowedContentTypes[mimeType]
	if !ok {
		// sniff by extension fallback for text types served as octet-stream
		ext, ok = extByFilename(filename)
		if !ok {
			return Document{}, fmt.Errorf("%w: %s", ErrUnsupportedType, mimeType)
		}
	}
	if size > MaxUploadBytes {
		return Document{}, ErrTooLarge
	}

	docID := uuid.NewString()
	key := ObjectKey(docID, ext)
	if err := storage.PutObject(ctx, key, content, size, mimeType); err != nil {
		return Document{}, fmt.Errorf("store object: %w", err)
	}

	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return Document{}, err
	}
	defer tx.Rollback(ctx)

	var doc Document
	err = tx.QueryRow(ctx, `
		INSERT INTO documents (id, workspace_id, uploaded_by, filename, mime_type, size_bytes, storage_key, status)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
		RETURNING id, workspace_id, filename, mime_type, size_bytes, status, created_at`,
		docID, wsID, uploadedBy, sanitizeFilename(filename), mimeType, size, key, StatusUploaded).
		Scan(&doc.ID, &doc.WorkspaceID, &doc.Filename, &doc.MimeType, &doc.SizeBytes, &doc.Status, &doc.CreatedAt)
	if err != nil {
		return Document{}, err
	}
	if _, err := tx.Exec(ctx,
		`INSERT INTO ingestion_jobs (document_id, workspace_id, status) VALUES ($1,$2,'PENDING')`,
		docID, wsID); err != nil {
		return Document{}, err
	}
	if err := tx.Commit(ctx); err != nil {
		return Document{}, err
	}
	return doc, nil
}

func (s *Store) List(ctx context.Context, wsID string) ([]Document, error) {
	rows, err := s.pool.Query(ctx, `
		SELECT id, workspace_id, filename, mime_type, size_bytes, status, created_at
		FROM documents WHERE workspace_id = $1 AND deleted_at IS NULL ORDER BY created_at DESC`, wsID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Document
	for rows.Next() {
		var d Document
		if err := rows.Scan(&d.ID, &d.WorkspaceID, &d.Filename, &d.MimeType, &d.SizeBytes, &d.Status, &d.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, d)
	}
	return out, rows.Err()
}

func (s *Store) ByID(ctx context.Context, id string) (Document, error) {
	var d Document
	err := s.pool.QueryRow(ctx, `
		SELECT id, workspace_id, filename, mime_type, size_bytes, status, created_at
		FROM documents WHERE id = $1 AND deleted_at IS NULL`, id).
		Scan(&d.ID, &d.WorkspaceID, &d.Filename, &d.MimeType, &d.SizeBytes, &d.Status, &d.CreatedAt)
	if errors.Is(err, pgx.ErrNoRows) {
		return Document{}, ErrNotFound
	}
	return d, err
}

// Delete soft-deletes a document (chunks stay but retrieval filters deleted).
func (s *Store) Delete(ctx context.Context, id string) error {
	tag, err := s.pool.Exec(ctx,
		`UPDATE documents SET deleted_at = now(), status = 'RETIRED', updated_at = now() WHERE id = $1 AND deleted_at IS NULL`, id)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNotFound
	}
	return nil
}

func (s *Store) SetStatus(ctx context.Context, id, status, errText string) error {
	tag, err := s.pool.Exec(ctx,
		`UPDATE documents SET status = $2, updated_at = now() WHERE id = $1`, id, status)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNotFound
	}
	if errText != "" {
		_, _ = s.pool.Exec(ctx,
			`UPDATE ingestion_jobs SET status='FAILED', error=$2, finished_at=now() WHERE document_id=$1`, id, errText)
	}
	return nil
}

var unsafeChars = regexp.MustCompile(`[^\w.\- ]`)

func sanitizeFilename(name string) string {
	name = path.Base(name)
	name = unsafeChars.ReplaceAllString(name, "_")
	if name == "" || name == "." || name == ".." {
		name = "upload"
	}
	return name
}

func extByFilename(filename string) (string, bool) {
	switch strings.ToLower(path.Ext(filename)) {
	case ".pdf":
		return ".pdf", true
	case ".docx":
		return ".docx", true
	case ".xlsx":
		return ".xlsx", true
	case ".txt":
		return ".txt", true
	case ".md", ".markdown":
		return ".md", true
	case ".csv":
		return ".csv", true
	case ".jpg", ".jpeg":
		return ".jpg", true
	case ".png":
		return ".png", true
	default:
		return "", false
	}
}
