#!/usr/bin/env bash
# Sovereign Workbench killer demo — end-to-end via the API.
set -euo pipefail
API="${API:-http://localhost:8080}"
EMAIL="${BOOTSTRAP_ADMIN_EMAIL:-admin@example.com}"
PASS="${BOOTSTRAP_ADMIN_PASSWORD:-Admin#Dev1}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> 1. login"
TOKEN=$(curl -s -X POST "$API/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')

echo "==> 2. org + workspace"
ORG=$(curl -s -X POST "$API/api/v1/organizations" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"name":"Reliability Demo"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
WS=$(curl -s -X POST "$API/api/v1/organizations/$ORG/workspaces" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"name":"Pump P-17 Evidence"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')

echo "==> 3. ingest confidential sources (no cloud, ever)"
for f in maintenance_manual.md equipment_inventory.csv daily_maintenance_logs.csv; do
  curl -s -X POST "$API/api/v1/workspaces/$WS/documents" -H "Authorization: Bearer $TOKEN" -F "file=@$DIR/$f" > /dev/null
  curl -s -X POST "${AI_URL:-http://localhost:8000}/internal/ingest/run" -H 'X-Internal-Secret: internal-dev-only-change-me' > /dev/null
done
echo "    3 documents ingested into workspace $WS"

echo "==> 4. grounded question (citations, local model)"
curl -s -X POST "$API/api/v1/workspaces/$WS/tasks" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"question":"Analyze the maintenance history of pump P-17. What is the likely cause of the repeated shutdowns?"}' \
  | python3 -c '
import json,sys
d=json.load(sys.stdin)
r=d.get("result") or {}
print("STATUS:", d["status"], "| confidence:", r.get("confidence"))
print("ANSWER:", (r.get("answer") or "")[:600])
print("CITATIONS:", r.get("citations"))
print("TASK_ID:", d["task_id"])' | tee /tmp/demo-answer.txt

echo "==> 5. report task (pauses for human approval)"
TASK=$(curl -s -X POST "$API/api/v1/workspaces/$WS/tasks" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"question":"Generate a maintenance action report for pump P-17"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["task_id"])')
echo "    task $TASK is now WAITING_FOR_APPROVAL"

echo "==> 6. approve → report generated; audit has every step"
curl -s -X POST "$API/api/v1/tasks/$TASK/approval" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"approved":true}' \
  | python3 -c 'import json,sys;d=json.load(sys.stdin);print("FINAL:",d["status"])'

echo "DONE — workspace: $WS"
echo "Open the UI at http://localhost:3000 to see it in the browser."
