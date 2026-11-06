"""Unit tests: confidence gate + planner (deterministic, no DB/model)."""

import pytest

from app.grounding.confidence import Decision, EvidenceItem, evaluate_evidence
from app.orchestration.planner import (
    MAX_STEPS,
    Plan,
    Step,
    can_transition,
    plan_for_question,
)
from app.tools.tools import ToolError, validate_readonly_sql


def test_gate_strong_evidence_answers() -> None:
    ev = [EvidenceItem("c1", 0.72, "ws1"), EvidenceItem("c2", 0.51, "ws1")]
    r = evaluate_evidence(ev, "ws1")
    assert r.decision is Decision.ANSWER and r.score == 0.72


def test_gate_weak_evidence_warns() -> None:
    r = evaluate_evidence([EvidenceItem("c1", 0.35, "ws1")], "ws1")
    assert r.decision is Decision.ANSWER_WITH_WARNING


def test_gate_no_evidence_refuses() -> None:
    r = evaluate_evidence([], "ws1")
    assert r.decision is Decision.REFUSE


def test_gate_foreign_workspace_never_counts() -> None:
    r = evaluate_evidence([EvidenceItem("c1", 0.95, "ws2")], "ws1")
    assert r.decision is Decision.REFUSE


def test_gate_revoked_never_counts() -> None:
    r = evaluate_evidence([EvidenceItem("c1", 0.95, "ws1", revoked=True)], "ws1")
    assert r.decision is Decision.REFUSE


def test_planner_simple_question_one_step() -> None:
    plan = plan_for_question("What happened with pump P-17?")
    assert [s.action for s in plan.steps] == ["document_search"]


def test_planner_report_question_adds_write_step() -> None:
    plan = plan_for_question("Generate a maintenance report from the logs")
    assert [s.action for s in plan.steps] == ["document_search", "report_generate"]


def test_planner_rejects_unknown_agent_and_oversize() -> None:
    with pytest.raises(Exception):
        Plan("g", [Step("s1", "hacker", "document_search")]).validate()
    with pytest.raises(Exception):
        Plan("g", [Step(f"s{i}", "retrieval", "document_search") for i in range(MAX_STEPS + 1)]).validate()


def test_task_transitions_validated() -> None:
    assert can_transition("PLANNING", "RUNNING")
    assert not can_transition("COMPLETED", "RUNNING")
    assert not can_transition("QUEUED", "COMPLETED")


def test_sql_readonly_rejects_writes() -> None:
    assert validate_readonly_sql("SELECT * FROM documents").endswith("documents")
    for bad in [
        "UPDATE documents SET status='X'",
        "DELETE FROM documents",
        "DROP TABLE users",
        "INSERT INTO documents VALUES (1)",
        "SELECT 1; DROP TABLE users",
        "ALTER TABLE users ADD COLUMN x int",
    ]:
        try:
            validate_readonly_sql(bad)
        except ToolError:
            continue
        raise AssertionError(f"must reject: {bad}")


def test_focus_evidence_keeps_only_close_top_hits() -> None:
    from app.orchestration.executor import focus_evidence

    ev = [{"score": s} for s in (0.49, 0.87, 0.80, 0.75, 0.74, 0.25)]
    assert [e["score"] for e in focus_evidence(ev)] == [0.87, 0.80, 0.75]
    assert [e["score"] for e in focus_evidence([{"score": 0.9}, {"score": 0.5}])] == [0.9]
    assert focus_evidence([{"score": 0.2}]) == [] and focus_evidence([]) == []


def test_verifier_split_numbers_parse_and_score() -> None:
    from app.grounding.verifier import is_absence, missing_numbers, parse_verdict, score, split_sentences

    assert split_sentences("Budget is 4.2 crore [1]. Leave is 24 days [2].\nThe cafeteria opens at 8:15 AM.") == [
        "Budget is 4.2 crore [1].",
        "Leave is 24 days [2].",
        "The cafeteria opens at 8:15 AM.",
    ]
    assert is_absence("The sources do not contain the answer.")
    assert is_absence("The documents don't mention who the CEO is.")
    assert not is_absence("No, passwords must be rotated every 90 days [1].")

    src = "[1] (hr.docx, page 2)\nWork from home is allowed two days per week. Cafeteria opens at 8:15 AM. Budget 4.2 crore."
    assert missing_numbers("You can work from home 2 days per week [1].", src) == set()
    assert missing_numbers("You can work from home three days per week [1].", src) == {"3"}
    assert missing_numbers("The cafeteria opens at 9 AM [1].", src) == {"9"}
    assert missing_numbers("The budget is 99 crore [1].", src) == {"99"}
    assert missing_numbers("The budget is 4.2 crore [1].", src) == set()

    from app.grounding.verifier import topic_overlap

    pw = "[1] (security.pdf, page 2)\nPasswords must be rotated every 90 days."
    assert topic_overlap("You can work from home two days per week [1].", pw) < 1 / 3
    assert topic_overlap("No, passwords must be rotated every 90 days [1].", pw) == 1.0

    assert parse_verdict("thinking... SUPPORTED? no.\nNOT_SUPPORTED") is False
    assert parse_verdict("SUPPORTED") is True and parse_verdict("unsure") is False

    ok, bad = {"supported": True}, {"supported": False}
    assert score([ok, bad], weak_evidence=False) == (0.5, "partially_verified")
    assert score([ok], weak_evidence=False) == (1.0, "verified")
    assert score([ok], weak_evidence=True)[0] == 0.7
    assert score([bad], weak_evidence=False) == (0.0, "unverified")
    assert score([], weak_evidence=False) == (0.0, "not_found")
