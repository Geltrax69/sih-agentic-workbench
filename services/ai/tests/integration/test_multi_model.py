"""Integration tests for the multi-model pipeline endpoint.

Runs against a fake OpenAI-compatible endpoint (no real model server needed):
- /internal/query/multi-model with two models fanning out over the same evidence
- graceful behavior when one model fails
- empty-workspace refusal path

Retrieval is stubbed in every test, so no postgres is required; the
workspace-scoping of the real retrieval is covered by unit tests of
search_workspace and by the existing auth integration suite.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

from app import multi_model
from app.config import settings
from app.main import app


class _FakeModelHandler(BaseHTTPRequestHandler):
    """Minimal OpenAI-compatible /v1/chat/completions + /v1/embeddings."""

    def log_message(self, *args) -> None:  # silence request logging
        pass

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        if self.path.endswith("/chat/completions"):
            model = "unknown"
            try:
                import json

                model = json.loads(body).get("model", "unknown")
            except Exception:  # noqa: BLE001
                pass
            if "failme" in model:
                self.send_response(500)
                self.end_headers()
                return
            import json
            content = json.dumps({"primary": "E1", "secondary": "NONE"})
            payload = (
                '{"choices":[{"message":{"role":"assistant","content":"'
                + content.replace('"', '\\"')
                + '"}}]}'
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload.encode())
        elif self.path.endswith("/embeddings"):
            payload = '{"data":[{"index":0,"embedding":[0.1,0.2,0.3]}]}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload.encode())
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture(scope="module")
def fake_model_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeModelHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()


@pytest.fixture()
def ai_client(fake_model_server, monkeypatch):
    monkeypatch.setattr(settings, "ai_base_url", fake_model_server)
    monkeypatch.setattr(settings, "ai_model", "model-a")
    monkeypatch.setattr(settings, "ai_multi_models", "model-a,model-hot")
    with TestClient(app) as client:
        yield client


def _internal(client: TestClient, path: str, payload: dict):
    return client.post(
        path,
        json=payload,
        headers={"X-Internal-Secret": settings.internal_api_secret or "test-secret"},
    )


def test_multi_model_requires_secret(ai_client) -> None:
    resp = ai_client.post(
        "/internal/query/multi-model",
        json={"workspace_id": "00000000-0000-0000-0000-000000000000", "question": "q"},
    )
    # 401 from the secret check, or 422 if header validation rejects first —
    # either way the request never reaches the pipeline.
    assert resp.status_code in {401, 422}


def test_multi_model_no_evidence_refuses(ai_client, monkeypatch) -> None:
    async def fake_retrieve(workspace_id: str, question: str, limit: int = 8):
        return []

    monkeypatch.setattr(multi_model, "retrieve", fake_retrieve)
    resp = _internal(
        ai_client,
        "/internal/query/multi-model",
        {"workspace_id": "00000000-0000-0000-0000-000000000000", "question": "anything"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["combined_answer"].startswith("I don't know")
    assert body["individual_answers"] == []


def test_multi_model_fans_out_and_merges(ai_client, monkeypatch) -> None:
    """Full path with a stubbed retrieval so no real indexed data is needed."""
    evidence = [
        {
            "chunk_id": "c1", "document_id": "d1", "filename": "manual.md",
            "chunk_index": 0, "location": "page 3",
            "content": "Over-temperature shutdowns are caused by coolant loss.", "score": 0.9,
        }
    ]

    async def fake_retrieve(workspace_id: str, question: str, limit: int = 8):
        return evidence

    monkeypatch.setattr(multi_model, "retrieve", fake_retrieve)
    resp = _internal(
        ai_client,
        "/internal/query/multi-model",
        {"workspace_id": "00000000-0000-0000-0000-000000000000", "question": "why shutdowns?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["models_used"] == ["model-a", "model-hot"]
    answers = {a["model"]: a for a in body["individual_answers"]}
    assert not answers["model-a"]["error"]
    assert "coolant" in answers["model-a"]["answer"]
    assert answers["model-a"]["citations"] == ["manual.md, page 3"]
    assert body["agreement"]["n_answered"] == 2
    assert body["agreement"]["pairs"][0]["overlap"] > 0
    assert body["combined_answer"]
    assert body["verification"]["decision"] in {"verified", "partially_verified", "unverified"}


def test_multi_model_one_failure_does_not_kill_run(ai_client, monkeypatch) -> None:
    async def fake_retrieve(workspace_id: str, question: str, limit: int = 8):
        return [
            {
                "chunk_id": "c1", "document_id": "d1", "filename": "manual.md",
                "chunk_index": 0, "location": "page 3",
                "content": "Coolant loss causes shutdowns.", "score": 0.9,
            }
        ]

    monkeypatch.setattr(multi_model, "retrieve", fake_retrieve)
    resp = _internal(
        ai_client,
        "/internal/query/multi-model",
        {
            "workspace_id": "00000000-0000-0000-0000-000000000000",
            "question": "why shutdowns?",
            "models": ["model-a", "failme"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    answers = {a["model"]: a for a in body["individual_answers"]}
    assert not answers["model-a"]["error"]
    assert answers["failme"]["error"]
    assert body["agreement"]["n_answered"] == 1
    assert body["combined_answer"]
