"""Integration tests for the AI service HTTP surface (no external deps)."""

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_reports_model_endpoint_state() -> None:
    with TestClient(app) as client:
        resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"ok", "degraded"}
    # Model endpoint will typically be down in CI; health must stay honest.
    assert "model_endpoint" in body["components"]


def test_ping_reports_model_config() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/v1/ai/ping")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "ai"
    assert body["provider"] == "openai_compatible"
