"""Knowledge graph (P1-F-009): workspace-scoped typed nodes/edges built during
ingestion and consultation. Security invariant: every node carries workspace_id
and every query filters by it — no cross-workspace traversal."""

from __future__ import annotations

import uuid

import psycopg


def record_document_graph(dsn: str, document_id: str, workspace_id: str, filename: str, chunk_ids: list[str]) -> None:
    """DOCUMENT node + DOCUMENT_CHUNK nodes wired with GENERATED_FROM edges."""
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            doc_node = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO knowledge_nodes (id, workspace_id, type, title, metadata, source_id)
                VALUES (%s,%s,'DOCUMENT',%s,%s,%s)
                """,
                (doc_node, workspace_id, filename, '{"kind": "document"}', document_id),
            )
            for cid in chunk_ids:
                chunk_node = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO knowledge_nodes (id, workspace_id, type, title, metadata, source_id)
                    VALUES (%s,%s,'DOCUMENT_CHUNK',%s,%s,%s)
                    """,
                    (chunk_node, workspace_id, f"{filename}#chunk", '{"kind": "chunk"}', cid),
                )
                cur.execute(
                    """
                    INSERT INTO knowledge_edges (workspace_id, from_node, to_node, type)
                    VALUES (%s,%s,%s,'GENERATED_FROM')
                    """,
                    (workspace_id, chunk_node, doc_node),
                )
        conn.commit()


def graph_neighbors(dsn: str, workspace_id: str, node_source_ids: list[str], limit: int = 10) -> list[dict]:
    """One-hop traversal scoped to the workspace. Used to attach provenance."""
    if not node_source_ids:
        return []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT n.id, n.type, n.title, e.type AS edge
                FROM knowledge_edges e
                JOIN knowledge_nodes n ON n.id = e.from_node OR n.id = e.to_node
                WHERE e.workspace_id = %s
                  AND (e.from_node::text = ANY(%s) OR e.to_node::text = ANY(%s))
                LIMIT %s
                """,
                (workspace_id, node_source_ids, node_source_ids, limit),
            )
            return [
                {"id": str(r[0]), "type": r[1], "title": r[2], "edge": r[3]}
                for r in cur.fetchall()
            ]
