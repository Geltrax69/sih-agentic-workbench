"""Unit tests for deterministic extraction/chunking."""

from app.extraction import chunk_text, extract_csv_rows, extract_text


def test_chunk_short_text_single_chunk() -> None:
    chunks = chunk_text("hello world", size=100, overlap=10)
    assert chunks == ["hello world"]


def test_chunk_empty_text() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_chunk_long_text_sizes_and_overlap() -> None:
    text = " ".join(f"sentence number {i} explains something." for i in range(200)).strip()
    chunks = chunk_text(text, size=400, overlap=50)
    assert len(chunks) > 1
    for c in chunks:
        assert 0 < len(c) <= 400
    # distinct content produces distinct chunks (no stuck-position loop)
    assert len(set(chunks)) == len(chunks)
    # coverage: first chunk starts at the beginning, last ends at the end
    assert text.startswith(chunks[0])
    assert text.endswith(chunks[-1])


def test_chunk_prefers_paragraph_boundary() -> None:
    para = "A" * 100
    text = (para + "\n\n" + para + "\n\n" + para)
    chunks = chunk_text(text, size=250, overlap=0)
    assert len(chunks) >= 2
    assert all(c.strip() for c in chunks)


def test_extract_csv_rows() -> None:
    rows = extract_csv_rows("pump,date\nP-17,2026-08-01\nP-17,2026-09-01\n")
    assert len(rows) == 2
    assert rows[0]["pump"] == "P-17"


def test_extract_plain_text() -> None:
    assert extract_text("text/plain", b"hello") == "hello"


def test_extract_unsupported_mime_raises() -> None:
    try:
        extract_text("application/zip", b"PK")
    except Exception:
        return
    raise AssertionError("unsupported mime must raise")
