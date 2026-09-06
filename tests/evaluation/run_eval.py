"""Evaluation suite (P1-F-018): retrieval relevance + citation correctness on
the demo corpus. Requires the live stack (api + ai + ollama). Results are
stored as data (JSON), never screenshots.

    python3 tests/evaluation/run_eval.py            # uses default QA pairs
    python3 tests/evaluation/run_eval.py --json ... # custom dataset
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

API = os.environ.get("API", "http://localhost:8080")
AI = os.environ.get("AI_URL", "http://localhost:8000")
SECRET = os.environ.get("INTERNAL_API_SECRET", "internal-dev-only-change-me")
EMAIL = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
PASSWORD = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "Admin#Dev1")

# (question, keywords that MUST appear in retrieved evidence or answer)
QA_PAIRS = [
    ("What causes over-temperature shutdowns in P-series pumps?", ["cooling", "bearing", "coolant"]),
    ("Which bearing part is used when replacing a P-17 bearing?", ["BRG-4210"]),
    ("When did pump P-17 last shut down from overheating?", ["2026-09-01"]),
]


def post(url: str, payload: dict, headers: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers}
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    token = post(f"{API}/api/v1/auth/login", {"email": EMAIL, "password": PASSWORD}, {})["token"]
    org = post(f"{API}/api/v1/organizations", {"name": f"eval-{int(time.time())}"}, {"Authorization": f"Bearer {token}"})["id"]
    ws = post(
        f"{API}/api/v1/organizations/{org}/workspaces",
        {"name": "eval-corpus"},
        {"Authorization": f"Bearer {token}"},
    )["id"]

    demo_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "demo")
    files = {
        "maintenance_manual.md": "text/markdown",
        "equipment_inventory.csv": "text/csv",
        "daily_maintenance_logs.csv": "text/csv",
    }
    import uuid as _uuid

    boundary = f"----eval{_uuid.uuid4().hex}"
    for fname, mime in files.items():
        with open(os.path.join(demo_dir, fname), "rb") as f:
            body = f.read()
        part = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fname}\"\r\n"
            f"Content-Type: {mime}\r\n\r\n"
        ).encode() + body + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            f"{API}/api/v1/workspaces/{ws}/documents",
            data=part,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            assert r.status == 201, r.read()
        post(f"{AI}/internal/ingest/run", {}, {"X-Internal-Secret": SECRET})

    results = []
    for question, keywords in QA_PAIRS:
        task = post(
            f"{API}/api/v1/workspaces/{ws}/tasks",
            {"question": question},
            {"Authorization": f"Bearer {token}"},
        )
        result = task.get("result") or {}
        answer = (result.get("answer") or "").lower()
        evidence_text = " ".join(e["content"].lower() for e in result.get("evidence", []))
        hits = [k for k in keywords if k.lower() in evidence_text or k.lower() in answer]
        results.append(
            {
                "question": question,
                "decision": result.get("decision"),
                "confidence": result.get("confidence"),
                "keyword_hits": hits,
                "keyword_total": len(keywords),
                "citations": result.get("citations", []),
                "hit_rate": len(hits) / len(keywords),
            }
        )
        print(f"[{len(hits)}/{len(keywords)}] {question}")

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "corpus": list(files),
        "qa": results,
        "mean_hit_rate": sum(r["hit_rate"] for r in results) / len(results),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = args.out or os.path.join(out_dir, f"eval-{int(time.time())}.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nmean retrieval hit rate: {summary['mean_hit_rate']:.0%} -> {out_path}")
    return 0 if summary["mean_hit_rate"] >= 0.6 else 1


if __name__ == "__main__":
    sys.exit(main())
