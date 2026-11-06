"""Text extraction and chunking for the ingestion pipeline.

Extraction supports: PDF (pypdf), DOCX (python-docx), XLSX (openpyxl),
PPTX (stdlib zip/xml), TXT/MD/CSV (plain). Each segment carries its location
(page / slide / sheet) so answers can cite it. Extracted text is DATA — it is never treated as
instructions (prompt-injection defense lives in the grounding layer).
"""

from __future__ import annotations

import csv
import io
import re

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

SUPPORTED_MIME = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/csv": ".csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
}


class ExtractionError(Exception):
    pass


def extract_segments(mime_type: str, data: bytes) -> list[tuple[str, str]]:
    """Extract (location, text) pairs, e.g. ("page 3", ...), so answers can cite where a fact is."""
    ext = SUPPORTED_MIME.get(mime_type)
    if ext is None:
        raise ExtractionError(f"unsupported mime type: {mime_type}")

    if ext == ".pdf":
        return _extract_pdf(data)
    if ext == ".docx":
        return _extract_docx(data)
    if ext == ".xlsx":
        return _extract_xlsx(data)
    if ext == ".pptx":
        return _extract_pptx(data)
    return [("", data.decode("utf-8", errors="replace"))]


def extract_text(mime_type: str, data: bytes) -> str:
    """Extract text from raw bytes by MIME type."""
    return "\n\n".join(t for _, t in extract_segments(mime_type, data)).strip()


def _extract_pdf(data: bytes) -> list[tuple[str, str]]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001 — any parse failure quarantines the doc
        raise ExtractionError(f"corrupt pdf: {exc}") from exc
    pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
    # Preserve source text, including repeated margin statements: a repeated
    # line can still be a fact. Paragraph ranking handles irrelevant metadata.
    return [(f"page {n}", _label_table_rows(text)) for n, text in enumerate(pages, 1)]


def _label_table_rows(text: str) -> str:
    """Label aligned numeric rows from layout extraction, without model inference.

    Only tables with at least three columns are recognized. Two-column chart
    axes and ambiguous layouts remain unchanged rather than becoming fake facts.
    """
    lines = text.splitlines()
    header: list[str] = []
    output = []
    for line in lines:
        cells = [c.strip() for c in re.split(r"\s{2,}", line.strip()) if c.strip()]
        numeric = sum(bool(re.fullmatch(r"[-+]?\d[\d,.:/%-]*", c)) for c in cells)
        if len(cells) >= 3 and numeric == 0 and all(len(c) < 45 for c in cells):
            header = cells
        elif header and len(cells) == len(header) and numeric >= len(cells) - 1:
            line = "Table row: " + "; ".join(f"{name} = {value}" for name, value in zip(header, cells, strict=True)) + "."
        elif line.strip() and len(cells) >= 3:
            header = []
        output.append(line.rstrip())
    return "\n".join(output)


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _extract_docx(data: bytes) -> list[tuple[str, str]]:
    from docx import Document as DocxDocument

    try:
        doc = DocxDocument(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"corrupt docx: {exc}") from exc
    # ponytail: .docx has no stored page numbers; count Word's saved page breaks
    # (lastRenderedPageBreak + manual breaks). Files never opened in Word read as page 1.
    pages: dict[int, list[str]] = {}
    page = 1
    for el in doc.element.body.iterchildren():
        if el.tag == _W + "p":
            text = "".join(t.text or "" for t in el.iter(_W + "t"))
        elif el.tag == _W + "tbl":
            text = "\n".join(
                " | ".join("".join(t.text or "" for t in tc.iter(_W + "t")).strip() for tc in tr.iter(_W + "tc"))
                for tr in el.iter(_W + "tr")
            )
        else:
            continue
        breaks = sum(1 for _ in el.iter(_W + "lastRenderedPageBreak")) + sum(
            1 for b in el.iter(_W + "br") if b.get(_W + "type") == "page"
        )
        if text.strip():
            pages.setdefault(page, []).append(text)
        page += breaks
    return [(f"page {n}", "\n".join(parts)) for n, parts in pages.items()]


def _extract_xlsx(data: bytes) -> list[tuple[str, str]]:
    from openpyxl import load_workbook

    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"corrupt xlsx: {exc}") from exc
    segments: list[tuple[str, str]] = []
    for sheet in wb.worksheets:
        rows: list[str] = []
        for n, row in enumerate(sheet.iter_rows(values_only=True), 1):
            cells = ["" if v is None else str(v) for v in row]
            if any(c.strip() for c in cells):
                rows.append(f"row {n}: " + " | ".join(cells))
        segments.append((f"sheet {sheet.title}", "\n".join(rows)))
    return segments


_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _extract_pptx(data: bytes) -> list[tuple[str, str]]:
    import posixpath
    import zipfile
    from xml.etree import ElementTree as ET

    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        rels = ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"corrupt pptx: {exc}") from exc
    targets = {r.get("Id"): r.get("Target") for r in rels}
    segments: list[tuple[str, str]] = []
    # slide order comes from presentation.xml, not file names
    for n, sld in enumerate(pres.iter(_P + "sldId"), 1):
        path = posixpath.normpath(posixpath.join("ppt", targets[sld.get(_R + "id")]))
        slide = ET.fromstring(z.read(path))
        lines = ["".join(t.text or "" for t in para.iter(_A + "t")) for para in slide.iter(_A + "p")]
        segments.append((f"slide {n}", "\n".join(line for line in lines if line.strip())))
    return segments


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
        next_start = max(end - overlap, start + 1)
        # Begin overlap at a full line or word, rather than mid-token.
        if overlap:
            boundary = text.find("\n", next_start, end)
            if boundary >= 0:
                next_start = boundary + 1
            elif next_start > 0 and not text[next_start - 1].isspace():
                boundary = next((i for i in range(next_start, end) if text[i].isspace()), end)
                next_start = min(boundary + 1, end)
        start = next_start
    return [c for c in chunks if c]
