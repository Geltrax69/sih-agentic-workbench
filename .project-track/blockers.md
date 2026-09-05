# Active Blockers

## BLOCK-001 — Local model endpoint unavailable

Status: OPEN
Impact: Project 1 agent/inference E2E work cannot run against a live model.

Evidence:
Forge baseline run 2026-09-06: connection refused on http://127.0.0.1:1234/v1
(LM Studio default). Ollama not confirmed running either.

Temporary workaround:
Unit/integration work with stubbed model adapter continues. Docker Compose
models health endpoint will report endpoint state. Do not mark release gate
complete while this is open.

Next action:
Start Ollama (or LM Studio) and set AI_BASE_URL in .env; verify
GET /api/v1/models/health turns green.
