"""Tools for the agent executor. Capability classes are enforced by the
executor: model output can never elevate a tool's risk class."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import psycopg
from psycopg.rows import dict_row


class ToolError(Exception):
    pass


READ_ONLY = "READ_ONLY"
COMPUTE = "COMPUTE"
WRITE = "WRITE"
DESTRUCTIVE = "DESTRUCTIVE"


@dataclass
class Tool:
    name: str
    description: str
    risk_class: str
    run: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


# --- document_search (READ_ONLY) ---

def make_document_search(search_fn) -> Tool:
    async def run(args: dict[str, Any]) -> dict[str, Any]:
        question = str(args.get("question", "")).strip()
        workspace_id = str(args.get("workspace_id", ""))
        if not question or not workspace_id:
            raise ToolError("question and workspace_id are required")
        return await search_fn(workspace_id, question, int(args.get("limit", 6)))

    return Tool("document_search", "Vector search over workspace documents", READ_ONLY, run)


# --- sql_readonly (READ_ONLY, hard-enforced) ---

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|grant|revoke|create|copy)\b", re.I
)


def validate_readonly_sql(sql: str) -> str:
    sql = sql.strip().rstrip(";")
    if not sql.lower().startswith("select"):
        raise ToolError("only SELECT statements are allowed")
    if _FORBIDDEN.search(sql):
        raise ToolError("write keywords are not allowed")
    if ";" in sql:
        raise ToolError("multiple statements are not allowed")
    return sql


def make_sql_readonly(dsn: str, row_limit: int = 200, timeout_ms: int = 5000) -> Tool:
    async def run(args: dict[str, Any]) -> dict[str, Any]:
        sql = validate_readonly_sql(str(args.get("sql", "")))
        # executed on a read-only transaction with a statement timeout
        def _query() -> list[dict]:
            with psycopg.connect(dsn, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SET statement_timeout = {int(timeout_ms)}")
                    cur.execute(sql)
                    return cur.fetchmany(row_limit)

        import asyncio

        rows = await asyncio.to_thread(_query)
        return {"rows": rows, "row_count": len(rows)}

    return Tool("sql_readonly", "Read-only SQL against workspace data", READ_ONLY, run)


# --- report_generate (WRITE: creates an artifact, requires approval) ---

def make_report_generate() -> Tool:
    async def run(args: dict[str, Any]) -> dict[str, Any]:
        title = str(args.get("title", "Report")).strip() or "Report"
        body = str(args.get("body", "")).strip()
        citations = args.get("citations") or []
        if not body:
            raise ToolError("report body is required")
        lines = [f"# {title}", "", body, "", "## Sources"]
        lines += [f"- [{i + 1}] {c}" for i, c in enumerate(citations)]
        return {"format": "markdown", "content": "\n".join(lines)}

    return Tool("report_generate", "Generate a cited markdown report", WRITE, run)


def default_tools(dsn: str, search_fn) -> dict[str, Tool]:
    search = make_document_search(search_fn)
    sql = make_sql_readonly(dsn)
    report = make_report_generate()
    return {t.name: t for t in (search, sql, report)}
