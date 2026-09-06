"""Text extraction and chunking for the ingestion pipeline.

Extraction supports: PDF (pypdf), DOCX (python-docx), XLSX (openpyxl),
TXT/MD/CSV (plain). Extracted text is DATA — it is never treated as
instructions (prompt-injection defense lives in the grounding layer).
"""

from __future__ import annotations

import csv
import io

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

SUPPORTED_MIME = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/csv": ".csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
}


class ExtractionError(Exception):
    pass


def extract_text(mime_type: str, data: bytes) -> str:
    """Extract text from raw bytes by MIME type."""
    ext = SUPPORTED_MIME.get(mime_type)
    if ext is None:
        raise ExtractionError(f"unsupported mime type: {mime_type}")

    if ext == ".pdf":
        return _extract_pdf(data)
    if ext == ".docx":
        return _extract_docx(data)
    if ext == ".xlsx":
        return _extract_xlsx(data)
    return data.decode("utf-8", errors="replace")


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001 — any parse failure quarantines the doc
        raise ExtractionError(f"corrupt pdf: {exc}") from exc
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages).strip()


def _extract_docx(data: bytes) -> str:
    from docx import Document as DocxDocument

    try:
        doc = DocxDocument(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"corrupt docx: {exc}") from exc
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            parts.append(" | ".join(cells))
    return "\n".join(parts).strip()


def _extract_xlsx(data: bytes) -> str:
    from openpyxl import load_workbook

    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"corrupt xlsx: {exc}") from exc
    parts: list[str] = []
    for sheet in wb.worksheets:
        parts.append(f"# sheet: {sheet.title}")
        for row in sheet.iter_rows(values_only=True):
            cells = ["" if v is None else str(v) for v in row]
            if any(c.strip() for c in cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts).strip()


def extract_csv_rows(text: str) -> list[dict[str, str]]:
    """Parse CSV text into dict rows (used by structured tools later)."""
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks on paragraph/sentence boundaries.

    Deterministic: no model involvement. Chunks shorter than `size` are
    returned as-is; longer text splits at the last boundary before `size`,
    with `overlap` characters of carry-over.
    """
    text = text.strip()
    if not text:
        return []

    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # prefer paragraph break, then sentence end, then hard cut
            window = text[start:end]
            cut = max(window.rfind("\n\n"), window.rfind("\n"), window.rfind(". "))
            if cut > size // 2:
                end = start + cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)  # always advance
    return [c for c in chunks if c]
