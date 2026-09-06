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
