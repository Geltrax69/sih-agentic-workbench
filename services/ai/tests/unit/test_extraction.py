"""Unit tests for deterministic extraction/chunking."""

import io

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


def _pdf(pages: list[str]) -> bytes:
    # minimal multi-page PDF, no deps
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % (3 + 2 * i) for i in range(len(pages))), len(pages))]
    for i, text in enumerate(pages):
        stream = b"BT /F1 12 Tf 40 700 Td (%s) Tj ET" % text.encode()
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>" % (4 + 2 * i, 3 + 2 * len(pages)))
        objs.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (i, o)
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)


def _pptx(slides: list[str]) -> bytes:
    import zipfile

    p = "http://schemas.openxmlformats.org/presentationml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        # list slides in reverse file order to prove presentation.xml order wins
        ids = "".join(f'<p:sldId id="{256 + i}" r:id="rId{i}"/>' for i in reversed(range(len(slides))))
        z.writestr("ppt/presentation.xml", f'<p:presentation xmlns:p="{p}" xmlns:r="{r}"><p:sldIdLst>{ids}</p:sldIdLst></p:presentation>')
        rels = "".join(f'<Relationship Id="rId{i}" Target="slides/slide{i + 1}.xml"/>' for i in range(len(slides)))
        z.writestr("ppt/_rels/presentation.xml.rels", f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>')
        for i, text in enumerate(slides):
            z.writestr(f"ppt/slides/slide{i + 1}.xml", f'<p:sld xmlns:p="{p}" xmlns:a="{a}"><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:sld>')
    return buf.getvalue()


def test_segments_carry_page_slide_sheet_locations() -> None:
    from docx import Document as DocxDocument
    from docx.enum.text import WD_BREAK
    from openpyxl import Workbook

    from app.extraction import extract_segments

    pdf = extract_segments("application/pdf", _pdf(["Alpha intro", "Leave is 24 days"]))
    assert [loc for loc, _ in pdf] == ["page 1", "page 2"] and "24 days" in pdf[1][1]

    d = DocxDocument()
    d.add_paragraph("Cover")
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    d.add_paragraph("Budget is 4.2 crore")
    buf = io.BytesIO(); d.save(buf)
    docx = extract_segments("application/vnd.openxmlformats-officedocument.wordprocessingml.document", buf.getvalue())
    assert docx[-1][0] == "page 2" and "4.2 crore" in docx[-1][1]

    wb = Workbook(); ws = wb.active; ws.title = "Sales"; ws.append(["region", "q1"]); ws.append(["North", 120])
    buf = io.BytesIO(); wb.save(buf)
    xlsx = extract_segments("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", buf.getvalue())
    assert xlsx[0][0] == "sheet Sales" and "row 2: North | 120" in xlsx[0][1]

    pptx = extract_segments("application/vnd.openxmlformats-officedocument.presentationml.presentation", _pptx(["first file", "second file"]))
    assert pptx == [("slide 1", "second file"), ("slide 2", "first file")]
