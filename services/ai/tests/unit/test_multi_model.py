"""Unit tests for the multi-model pipeline (no live model endpoint needed)."""

from app.multi_model import (
    ModelAnswer,
    agreement_matrix,
    extract_citations,
    jaccard,
    resolve_models,
)
from app.config import settings


def test_resolve_models_explicit_wins():
    assert resolve_models(["m1", "m2"]) == ["m1", "m2"]


def test_resolve_models_env_fallback(monkeypatch):
    monkeypatch.setattr(settings, "ai_multi_models", "a, b ,,c")
    assert resolve_models(None) == ["a", "b", "c"]


def test_resolve_models_default_single(monkeypatch):
    monkeypatch.setattr(settings, "ai_multi_models", "")
    assert resolve_models(None) == [settings.ai_model]


def test_jaccard_identical_and_disjoint():
    assert jaccard("the pump overheats", "the pump overheats") == 1.0
    assert jaccard("bearing coolant", "photograph sunset") == 0.0


def test_agreement_matrix_pairs():
    answers = [
        ModelAnswer(model="a", answer="coolant pump bearing failure"),
        ModelAnswer(model="b", answer="coolant pump bearing failure"),
        ModelAnswer(model="c", answer=""),
    ]
    m = agreement_matrix(answers)
    assert m["n_answered"] == 2
    assert len(m["pairs"]) == 1
    assert m["pairs"][0]["overlap"] == 1.0
    assert m["mean_overlap"] == 1.0


def test_extract_citations_maps_to_evidence():
    evidence = [
        {"filename": "manual.md", "location": "page 3"},
        {"filename": "inventory.csv", "location": ""},
    ]
    cites = extract_citations("Bearing is [1] and stock [2]. Fake [7].", evidence)
    assert cites == ["manual.md, page 3", "inventory.csv"]
