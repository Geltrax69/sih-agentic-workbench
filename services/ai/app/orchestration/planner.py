"""Deterministic planner + capability-secured executor + task state machine.

Plan shape: bounded DAG of steps with known agents/tools only. The executor
runs each step through the tool registry, enforcing risk classes: WRITE and
DESTRUCTIVE tools pause the task in WAITING_FOR_APPROVAL until a human
decides. Task states are validated transitions, persisted for replay.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.grounding.confidence import Decision, EvidenceItem, evaluate_evidence
from app.tools.tools import DESTRUCTIVE, READ_ONLY, WRITE

# --- states ---

QUEUED = "QUEUED"
PLANNING = "PLANNING"
RUNNING = "RUNNING"
WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
VERIFYING = "VERIFYING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"

VALID_TRANSITIONS: dict[str, set[str]] = {
    QUEUED: {PLANNING, CANCELLED},
    PLANNING: {RUNNING, FAILED, CANCELLED},
    RUNNING: {WAITING_FOR_APPROVAL, VERIFYING, COMPLETED, FAILED, CANCELLED},
    WAITING_FOR_APPROVAL: {RUNNING, CANCELLED},
    VERIFYING: {COMPLETED, FAILED},
    FAILED: set(),
    COMPLETED: set(),
    CANCELLED: set(),
}

MAX_STEPS = 8

KNOWN_AGENTS = {"supervisor", "retrieval", "document", "data", "report", "verification"}


class PlanError(Exception):
    pass


@dataclass
class Step:
    key: str
    agent: str
    action: str  # tool name
    args: dict = field(default_factory=dict)


@dataclass
class Plan:
    goal: str
    steps: list[Step]

    def validate(self) -> None:
        if not self.steps:
            raise PlanError("empty plan")
        if len(self.steps) > MAX_STEPS:
            raise PlanError(f"plan exceeds {MAX_STEPS} steps")
        for s in self.steps:
            if s.agent not in KNOWN_AGENTS:
                raise PlanError(f"unknown agent: {s.agent}")


def plan_for_question(question: str) -> Plan:
    """Deterministic MVP plan: retrieve evidence, then (only if the user asked
    for an artifact) produce a report requiring approval. No free-form LLM
    planning loop; the structure is fixed and auditable."""
    wants_report = any(
        w in question.lower() for w in ("report", "summarize", "summary", "generate a")
    )
    steps = [Step("s1", "retrieval", "document_search", {"question": question})]
    if wants_report:
        steps.append(Step("s2", "report", "report_generate", {}))
    plan = Plan(goal=question, steps=steps)
    plan.validate()
    return plan


def can_transition(current: str, nxt: str) -> bool:
    return nxt in VALID_TRANSITIONS.get(current, set())
