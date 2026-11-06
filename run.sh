#!/usr/bin/env bash
# Start the tested LM Studio + Docker development setup from any directory.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

trap 'printf "\nStartup failed at line %s. Inspect services with:\n  cd %q && docker compose logs --tail=80 api ai web\n" "$LINENO" "$ROOT" >&2' ERR

for command_name in docker curl python3; do
  command -v "$command_name" >/dev/null || { echo "Required command missing: $command_name" >&2; exit 1; }
done
if ! command -v lms >/dev/null && [[ -x "$HOME/.lmstudio/bin/lms" ]]; then
  export PATH="$HOME/.lmstudio/bin:$PATH"
fi
command -v lms >/dev/null || { echo 'Install LM Studio and enable its lms CLI first.' >&2; exit 1; }
[[ -f .env ]] || { echo 'Missing .env. Configure it from .env.example before starting.' >&2; exit 1; }
docker compose version >/dev/null

if ! docker info >/dev/null 2>&1; then
  echo 'Starting Docker Desktop…'
  if [[ "$(uname -s)" == Darwin ]]; then
    open -a Docker
  else
    echo 'Start the Docker daemon, then run this script again.' >&2
    exit 1
  fi
  docker_ready=false
  for ((attempt=0; attempt<90; attempt++)); do
    if docker info >/dev/null 2>&1; then docker_ready=true; break; fi
    sleep 2
  done
  [[ "$docker_ready" == true ]] || { echo 'Docker did not become ready within 180 seconds.' >&2; exit 1; }
fi

# Read only non-secret settings from Compose; never execute/source .env as shell code.
settings="$(docker compose config --format json | python3 -c '
import json, sys
c = json.load(sys.stdin); s = c["services"]; e = s["ai"]["environment"]
required = {"eval-minicpm5-1b", "eval-gemma4-e4b"}
if set(e.get("AI_MULTI_MODELS", "").split(",")) != required:
    sys.exit("Set AI_MULTI_MODELS=eval-minicpm5-1b,eval-gemma4-e4b in .env.")
if e.get("AI_BASE_URL", "").rstrip("/") != "http://host.docker.internal:1234/v1":
    sys.exit("Set AI_BASE_URL=http://host.docker.internal:1234/v1 in .env.")
for service, target in [("web", None), ("api", 8080), ("ai", 8000)]:
    ports = s[service]["ports"]
    p = next(p for p in ports if target is None or int(p["target"]) == target)
    print(p["published"])
')"
WEB_PORT="$(printf '%s\n' "$settings" | sed -n '1p')"
API_PORT="$(printf '%s\n' "$settings" | sed -n '2p')"
AI_PORT="$(printf '%s\n' "$settings" | sed -n '3p')"

load_model() {
  local model_key="$1" identifier="$2"
  shift 2
  if lms ps --json | python3 -c 'import json,sys; sys.exit(0 if any(m["identifier"] == sys.argv[1] for m in json.load(sys.stdin)) else 1)' "$identifier"; then
    echo "Already loaded: $identifier"
  else
    lms load "$model_key" --identifier "$identifier" --yes "$@"
  fi
}

echo 'Loading the two answer models and document embedder…'
load_model minicpm5-1b eval-minicpm5-1b --context-length 8192
load_model gemma-4-e4b-it-obliterated eval-gemma4-e4b --context-length 8192
load_model text-embedding-nomic-embed-text-v1.5 eval-nomic

if ! lms server status --json | python3 -c 'import json,sys; s=json.load(sys.stdin); sys.exit(0 if s.get("running") and s.get("port")==1234 else 1)'; then
  lms server start --port 1234
fi
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:1234/v1/models >/dev/null

echo 'Building and starting the application…'
docker compose up -d --build

wait_for_url() {
  local url="$1" label="$2"
  echo "Waiting for ${label}…"
  for ((attempt=0; attempt<120; attempt++)); do
    if curl --fail --silent --max-time 3 "$url" >/dev/null 2>&1; then return 0; fi
    sleep 2
  done
  echo "$label did not become ready: $url" >&2
  return 1
}
wait_for_url "http://127.0.0.1:$API_PORT/healthz" API
wait_for_url "http://127.0.0.1:$AI_PORT/healthz" 'AI service'
wait_for_url "http://127.0.0.1:$WEB_PORT/" UI

printf '\nReady: http://localhost:%s\n' "$WEB_PORT"
echo 'Sign in using BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD from .env.'
echo 'Upload your PDF, wait for ingestion, and enable “Compare local models”.'
echo 'Logs: docker compose logs -f api ai web'
echo 'Stop: docker compose down (preserves stored data; LM Studio stays running)'
if [[ "${NO_BROWSER:-0}" != 1 ]]; then
  if [[ "$(uname -s)" == Darwin ]]; then
    open "http://localhost:$WEB_PORT" || true
  elif command -v xdg-open >/dev/null; then
    xdg-open "http://localhost:$WEB_PORT" >/dev/null 2>&1 || true
  fi
fi
