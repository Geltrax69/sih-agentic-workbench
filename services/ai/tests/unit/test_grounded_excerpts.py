"""Regressions for fabricated citations, wrong-source verification and retrieval gaps."""
import json
import asyncio

import pytest

from app import models_client, multi_model
from app.grounding import excerpts, verifier
from app.retrieval import select_evidence

BLOCK = "[1] (manual.pdf, page 1)\nThe coolant limit is 45 degrees.\n\n[2] (manual.pdf, page 2)\nInspect bearings every 30 days."


def test_excerpts_reject_invented_text_wrong_source_and_out_of_range():
    for quote in [
        {"source": 1, "text": "The coolant limit is 90 degrees."},
        {"source": 2, "text": "The coolant limit is 45 degrees."},
        {"source": 7, "text": "The coolant limit is 45 degrees."},
    ]:
        with pytest.raises(ValueError):
            excerpts.render(json.dumps({"quotes": [quote]}), BLOCK)
    assert excerpts.render('{"quotes": []}', BLOCK) == excerpts.REFUSAL


def test_source_bibliography_does_not_create_output_citations():
    block = multi_model.evidence_block([{"filename": "paper.pdf", "content": "The method uses vectors. [6]"}])
    answer = excerpts.render(json.dumps({"quotes": [{"source": 1, "text": "The method uses vectors. (document reference 6)"}]}), block)
    assert "[6]" not in answer
    assert multi_model.extract_citations(answer, [{"filename": "paper.pdf"}]) == ["paper.pdf"]


@pytest.mark.asyncio
async def test_exact_quote_verification_needs_no_model(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Exact source excerpts must not require a judge")
    monkeypatch.setattr(models_client, "generate", forbidden)
    answer = excerpts.render(json.dumps({"quotes": [{"source": 1, "text": "The coolant limit is 45 degrees."}]}), BLOCK)
    claims = await verifier.verify(BLOCK, "What limit?", answer)
    assert len(claims) == 1 and claims[0]["supported"]


@pytest.mark.asyncio
async def test_number_in_other_source_cannot_validate_wrong_citation(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Wrong-source numbers should be rejected before model judging")
    monkeypatch.setattr(models_client, "generate", forbidden)
    claims = await verifier.verify(BLOCK, "What limit?", "The coolant limit is 30 degrees [1].")
    assert not claims[0]["supported"]
    assert "30" in claims[0]["reason"]


def test_ambiguous_or_repetitive_verdict_cannot_pass():
    assert verifier.parse_verdict("SUPPORTED")
    assert not verifier.parse_verdict("NOT_SUPPORTED then SUPPORTED")
    assert not verifier.parse_verdict("UNSUPPORTED")
    assert not verifier.parse_verdict("random words " * 100 + "SUPPORTED")


def test_model_selects_ids_and_cannot_rewrite_source_text():
    assert excerpts.render_selection('{"primary": "E2", "secondary": "NONE"}', BLOCK) == "Inspect bearings every 30 days. [2]"
    assert excerpts.render_selection('{"primary": "NONE", "secondary": "NONE"}', BLOCK) == excerpts.REFUSAL
    for raw in ['{"spans": [999]}', '{"spans": [true]}', '{"spans": [1], "answer": "Invented"}']:
        with pytest.raises(ValueError):
            excerpts.render_selection(raw, BLOCK)


@pytest.mark.asyncio
async def test_slow_verification_is_cancelled_and_cannot_pass(monkeypatch):
    cancelled = []
    async def slow(*args, **kwargs):
        try:
            await asyncio.sleep(60)
        finally:
            cancelled.append(True)
    monkeypatch.setattr(models_client, "generate", slow)
    monkeypatch.setattr(verifier, "VERIFY_TIMEOUT_SECONDS", .01)
    claims = await verifier.verify(BLOCK, "What limit?", "Coolant may reach a limit of 45 degrees [1].")
    assert cancelled and not claims[0]["supported"]
    assert "TimeoutError" in claims[0]["reason"]


@pytest.mark.asyncio
async def test_judge_failure_is_retained_as_unsupported_claim(monkeypatch):
    async def failed(*args, **kwargs):
        assert kwargs["max_tokens"] == 64
        assert kwargs["reasoning_effort"] == "none"
        raise models_client.ModelError("token budget exhausted")
    monkeypatch.setattr(models_client, "generate", failed)
    claims = await verifier.verify(BLOCK, "What limit?", "Coolant may reach a limit of 45 degrees [1].")
    assert not claims[0]["supported"]
    assert "unavailable" in claims[0]["reason"]


@pytest.mark.asyncio
async def test_all_generators_failing_cannot_trigger_synthesis(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Do not generate an answer from failed candidates")
    monkeypatch.setattr(models_client, "generate", forbidden)
    assert await multi_model.synthesize("m", BLOCK, "What limit?", [
        multi_model.ModelAnswer(model="a", answer="", error="offline"),
    ]) == excerpts.REFUSAL


@pytest.mark.asyncio
async def test_default_union_retains_complementary_facts_without_another_model(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Default combination must not call a synthesizer model")
    monkeypatch.setattr(models_client, "generate", forbidden)
    answer = await multi_model.synthesize("m", BLOCK, "What limits and inspections?", [
        multi_model.ModelAnswer(model="a", answer="The coolant limit is 45 degrees. [1]"),
        multi_model.ModelAnswer(model="b", answer="Inspect bearings every 30 days. [2]"),
    ])
    assert "45 degrees" in answer and "30 days" in answer


@pytest.mark.asyncio
async def test_positive_value_is_not_an_exact_quote_of_negative_value(monkeypatch):
    calls = []
    async def reject(*args, **kwargs):
        calls.append(True)
        return "NOT_SUPPORTED"
    monkeypatch.setattr(models_client, "generate", reject)
    claims = await verifier.verify("[1] (manual.pdf)\n-45 degrees is the coolant limit.", "What limit?", "45 degrees is the coolant limit. [1]")
    assert calls and not claims[0]["supported"]


def test_lexical_matching_keeps_specific_default_paragraph():
    rows = [{"id": str(i), "content": "A general generation pilot compares temperatures and tokens.", "score": .9-i*.01} for i in range(8)]
    rows += [{"id": "answer", "content": "The normal task generation temperature is 0.3 and maximum output is 800 tokens.", "score": .65}]
    selected = select_evidence("What normal task generation temperature and maximum output tokens are used?", rows)
    assert any(r["id"] == "answer" for r in selected)
    assert all(r["score"] >= .3 for r in selected)


def test_table_layout_preserves_header_and_row_values():
    from io import BytesIO
    from reportlab.pdfgen.canvas import Canvas
    from app.extraction import extract_segments

    buf = BytesIO()
    canvas = Canvas(buf)
    for y, values in [(750, ("Clients", "Requests/s", "p95 ms")), (730, ("50", "2823.4", "32.4"))]:
        for x, value in zip((40, 190, 350), values):
            canvas.drawString(x, y, value)
    canvas.save()
    text = extract_segments("application/pdf", buf.getvalue())[0][1]
    assert "Clients" in text and "Requests/s" in text
    assert any("50" in line and "2823.4" in line and "32.4" in line for line in text.splitlines())
    assert "Requests/s = 2823.4" in text and "p95 ms = 32.4" in text


def test_missing_requested_attribute_cannot_be_replaced_by_related_fact():
    block = "[1] (manual.md)\nThe bearing is BRG-500. Tighten it to 40 Nm. Inspect it after 30 days."
    assert excerpts.candidate_ids(block, "What is the replacement bearing price?") == []
    assert excerpts.candidate_ids(block, "On what date was the bearing last serviced?") == []
    assert excerpts.candidate_ids(block, "What serial number was assigned to this pump?") == []
    assert excerpts.candidate_ids(block, "Which bearing and tightening torque are specified?")


def test_count_requires_the_asked_entity_not_an_unrelated_number():
    block = "[1] (report.pdf)\nThe benchmark ran 100 requests with no errors."
    assert excerpts.candidate_ids(block, "How many helicopters have been delivered?") == []
    assert excerpts.candidate_ids(block, "How many requests were run in the benchmark?")


def test_paragraph_retains_qualification_and_never_returns_tiny_tail_fragment():
    block = "[1] (report.pdf)\nThe model claimed a deletion. The claim was unsupported. No files were deleted.\n\ndeleted."
    spans = excerpts.choices(block)
    assert len(spans) == 1
    assert "No files were deleted" in spans[0]["text"]


def test_page_diversity_and_context_expansion_stay_in_document():
    from app.retrieval import expand_context
    rows = [
        {"document_id": "a", "location": "page 1", "chunk_index": i, "content": "Pump operating limit.", "score": .9-i*.01}
        for i in range(4)
    ]
    rows.append({"document_id": "a", "location": "page 2", "chunk_index": 4, "content": "Pump operating warning.", "score": .7})
    selected = select_evidence("Pump operating limit", rows)
    assert len({r["location"] for r in selected}) == 2
    foreign = {"document_id": "foreign", "location": "page 1", "chunk_index": 1, "content": "PRIVATE OTHER DOCUMENT", "score": .99}
    expanded = expand_context([rows[0]], rows+[foreign])
    assert "PRIVATE" not in expanded[0]["content"]


def test_question_ranking_is_the_order_shown_to_the_model():
    block = "[1] (study.pdf)\nThe method uses two seeds and records model outputs.\n\nThe random seeds used were 11 and 37."
    ids = excerpts.candidate_ids(block, "Which two random seeds were used?")
    prompt = excerpts.selection_prompt(block, "Which two random seeds were used?")
    assert ids[0] == "E2"
    assert prompt.index("E2:") < prompt.index("E1:")


def test_storage_inflections_match_without_hand_written_suffix_rules():
    from app.retrieval import terms
    assert terms("stored") == terms("stores")
    assert terms("tightening") == terms("tighten")


def test_page_context_reaches_table_above_chart():
    from app.retrieval import expand_context
    rows = [{"document_id": "a", "location": "page 2", "chunk_index": i,
             "content": "Table row: Clients = 100; Rate = 2100." if i == 2 else f"Text chunk {i}.", "score": .8}
            for i in range(8)]
    expanded = expand_context([rows[5]], rows)
    assert "Clients = 100" in expanded[0]["content"]


def test_explicit_numeric_row_condition_excludes_other_rows():
    block = "[1] (capacity.pdf)\nTable row: Users = 10; Latency = 8.2.\n\nTable row: Users = 25; Latency = 12.3."
    assert excerpts.candidate_ids(block, "At 25 active users, what latency was measured?") == ["E2"]
    assert set(excerpts.candidate_ids(block, "At 10 or 25 users, what latency was measured?")) == {"E1", "E2"}
