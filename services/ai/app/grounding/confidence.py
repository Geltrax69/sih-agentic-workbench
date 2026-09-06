"""Confidence gate — ported and generalized from Forge (agent/confidence.py).

Philosophy preserved verbatim: no evidence means refuse; tokens are never
spent to hallucinate. Evidence scoring comes from observable retrieval signal
(similarity scores from pgvector), not model self-assessment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Decision(str, Enum):
    ANSWER = "answer"
    ANSWER_WITH_WARNING = "answer_with_warning"
    REFUSE = "refuse"


# Thresholds chosen from observed pgvector cosine scores on the demo corpus.
STRONG = 0.45
WEAK = 0.30


@dataclass
class EvidenceItem:
    source_id: str
    score: float
    workspace_id: str | None = None
    revoked: bool = False
    stale: bool = False


@dataclass
class ConfidenceResult:
    score: float
    decision: Decision
    reasons: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)


def evaluate_evidence(evidence: list[EvidenceItem], expected_workspace: str) -> ConfidenceResult:
    """Score evidence; never count foreign-workspace or revoked items."""
    usable = [
        e
        for e in evidence
        if not e.revoked and e.workspace_id == expected_workspace
    ]
    blocked = len(evidence) - len(usable)
    reasons: list[str] = []
    if blocked:
        reasons.append(f"{blocked} evidence item(s) excluded (foreign workspace or revoked)")

    if not usable:
        return ConfidenceResult(0.0, Decision.REFUSE, reasons + ["no usable evidence"], [])

    best = max(usable, key=lambda e: e.score)
    score = best.score
    source_ids = [e.source_id for e in usable if e.score >= WEAK]

    if any(e.stale for e in usable[:3]):
        reasons.append("some evidence is stale")

    if score >= STRONG:
        return ConfidenceResult(score, Decision.ANSWER, reasons, source_ids)
    if score >= WEAK:
        reasons.append("evidence is weak; answer cautiously")
        return ConfidenceResult(score, Decision.ANSWER_WITH_WARNING, reasons, source_ids)
    reasons.append("best evidence below refusal threshold")
    return ConfidenceResult(score, Decision.REFUSE, reasons, source_ids)
