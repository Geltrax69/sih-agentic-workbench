"""Ingestion pipeline: extract -> chunk -> embed -> index (pgvector).

Statuses: UPLOADED -> PROCESSING -> INDEXED | FAILED
This service owns the AI-side tables (document_chunks) only; document rows
are updated via status writes scoped to workspace_id.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass

import psycopg
from psycopg.rows import dict_row

from app import models_client
from app.extraction import CHUNK_OVERLAP, CHUNK_SIZE, chunk_text, extract_segments

log = logging.getLogger("ingest")


@dataclass
class IngestResult:
    document_id: str
    status: str
    chunks: int


class IngestPipeline:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def next_pending(self) -> dict | None:
        """Fetch the oldest pending ingestion job (simple FIFO, one at a time)."""
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT j.id AS job_id, d.id AS document_id, d.workspace_id,
                           d.mime_type, d.storage_key, d.filename, d.status AS doc_status
                    FROM ingestion_jobs j
                    JOIN documents d ON d.id = j.document_id
                    WHERE j.status = 'PENDING' AND d.status = 'UPLOADED' AND d.deleted_at IS NULL
                    ORDER BY j.created_at
                    LIMIT 1
                    FOR UPDATE OF j SKIP LOCKED
                    """
                )
                row = cur.fetchone()
                if row is None:
                    return None
                cur.execute(
                    "UPDATE ingestion_jobs SET status='RUNNING', started_at=now() WHERE id=%s",
                    (row["job_id"],),
                )
                cur.execute("UPDATE documents SET status='PROCESSING' WHERE id=%s", (row["document_id"],))
                conn.commit()
                return row

    async def run_pending_one(self, embed_fn=None) -> IngestResult | None:
        """Process one pending document end-to-end. embed_fn injectable for tests."""
        job = self.next_pending()
        if job is None:
            return None
        embed_fn = embed_fn or models_client.embed

        try:
            segments = self._load_and_extract(job["storage_key"], job["mime_type"], job["document_id"])
            # chunk within each page/slide/sheet so every chunk has one location
            located = [(loc, c) for loc, text in segments for c in chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)]
            locations = [loc for loc, _ in located]
            chunks = [c for _, c in located]
            if not chunks:
                raise ValueError("no extractable text")
            vectors = await embed_fn(chunks)
            if len(vectors) != len(chunks):
                raise ValueError("embedding count mismatch")
            chunk_ids = self._store_chunks(job["document_id"], job["workspace_id"], chunks, vectors, locations)
            try:
                from app.knowledge.graph import record_document_graph

                record_document_graph(
                    self.dsn, job["document_id"], job["workspace_id"],
                    job.get("filename", ""), chunk_ids,
                )
            except Exception as exc:  # noqa: BLE001 — graph is additive, must not fail ingestion
                log.warning("graph recording failed for %s: %s", job["document_id"], exc)
            self._finish(job, "INDEXED", "")
            return IngestResult(job["document_id"], "INDEXED", len(chunks))
        except Exception as exc:  # noqa: BLE001 — pipeline must record failure, not crash
            log.warning("ingestion failed for %s: %s", job["document_id"], exc)
            self._finish(job, "FAILED", str(exc)[:500])
            return IngestResult(job["document_id"], "FAILED", 0)

    def _load_and_extract(self, storage_key: str, mime_type: str, document_id: str) -> list[tuple[str, str]]:
        """Load the object from MinIO via the Go API's S3 credentials."""
        from app.config import settings

        # Pull object via MinIO S3 API using service credentials
        import boto3  # local import: only needed at runtime path

        endpoint = settings.s3_endpoint or "http://localhost:9000"
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )
        obj = s3.get_object(Bucket=settings.s3_bucket, Key=storage_key)
        data = obj["Body"].read()
        return extract_segments(mime_type, data)

    def _store_chunks(self, document_id: str, workspace_id: str, chunks: list[str], vectors: list[list[float]], locations: list[str]) -> list[str]:
        chunk_ids: list[str] = []
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM document_chunks WHERE document_id = %s", (document_id,))
                for idx, (content, vec, loc) in enumerate(zip(chunks, vectors, locations, strict=True)):
                    chunk_ids.append(str(uuid.uuid4()))
                    cur.execute(
                        """
                        INSERT INTO document_chunks (id, document_id, workspace_id, chunk_index, location, content, token_count, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                        """,
                        (
                            chunk_ids[-1],
                            document_id,
                            workspace_id,
                            idx,
                            loc,
                            content,
                            len(content) // 4,
                            "[" + ",".join(f"{v:.6f}" for v in vec) + "]",
                        ),
                    )
            conn.commit()
        return chunk_ids

    def _finish(self, job: dict, status: str, err: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ingestion_jobs SET status=%s, error=%s, finished_at=now() WHERE id=%s",
                    ("DONE" if status == "INDEXED" else "FAILED", err, job["job_id"]),
                )
                cur.execute("UPDATE documents SET status=%s WHERE id=%s", (status, job["document_id"]))
            conn.commit()


def search_workspace(dsn: str, workspace_id: str, query_vector: list[float], limit: int = 6, question: str = "") -> list[dict]:
    """Workspace-scoped vector search. The workspace filter is mandatory —
    no cross-workspace retrieval can ever occur through this path."""
    vec = "[" + ",".join(f"{v:.6f}" for v in query_vector) + "]"
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            if question:
                import re

                # PostgreSQL applies the same English stemming to both sides.
                # Python's lightweight ranking stems must not be used as raw
                # lexemes with the unstemmed `simple` dictionary.
                lexical_query = " | ".join(sorted(set(re.findall(r"[a-z0-9]+", question.lower()))))
                if lexical_query:
                    # Every candidate channel uses the same authorization scope.
                    cur.execute(
                        """
                        WITH scoped AS (
                            SELECT c.id, c.document_id, d.filename, c.chunk_index,
                                   c.location, c.content, c.embedding
                            FROM document_chunks c JOIN documents d ON d.id = c.document_id
                            WHERE c.workspace_id = %s AND d.deleted_at IS NULL
                        ), vector_hits AS (
                            SELECT id FROM scoped ORDER BY embedding <=> %s::vector LIMIT %s
                        ), lexical_hits AS (
                            SELECT id FROM scoped
                            WHERE to_tsvector('english', content) @@ to_tsquery('english', %s)
                            ORDER BY ts_rank_cd(to_tsvector('english', content), to_tsquery('english', %s)) DESC
                            LIMIT %s
                        ), hits AS (SELECT id FROM vector_hits UNION SELECT id FROM lexical_hits)
                        SELECT s.id, s.document_id, s.filename, s.chunk_index, s.location, s.content,
                               1 - (s.embedding <=> %s::vector) AS score,
                               s.id NOT IN (SELECT id FROM hits) AS context_only
                        FROM scoped s WHERE s.id IN (SELECT id FROM hits) OR EXISTS (
                            SELECT 1 FROM scoped h JOIN hits ON hits.id = h.id
                            WHERE h.document_id = s.document_id AND h.location = s.location
                              AND abs(h.chunk_index - s.chunk_index) <= 4
                        )
                        ORDER BY score DESC
                        """,
                        (workspace_id, vec, limit, lexical_query, lexical_query, limit, vec),
                    )
                    return cur.fetchall()
            cur.execute(
                """
                SELECT c.id, c.document_id, d.filename, c.chunk_index, c.location, c.content,
                       1 - (c.embedding <=> %s::vector) AS score
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.workspace_id = %s AND d.deleted_at IS NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (vec, workspace_id, vec, limit),
            )
            return cur.fetchall()


def chunk_json(chunks: list[str]) -> str:
    return json.dumps({"chunks": chunks})
