AI_PY := $(shell cd services/ai && if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

.PHONY: dev dev-build dev-down dev-logs build lint test test-unit test-integration test-e2e test-security test-performance seed clean

# ---------- development ----------

dev: ## start the full stack with docker compose
	docker compose up -d --build
	@echo "web:   http://localhost:$${WEB_PORT:-3000}"
	@echo "api:   http://localhost:$${API_PORT:-8080}/healthz"
	@echo "ai:    http://localhost:$${AI_SERVICE_PORT:-8000}/healthz"

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f api ai

# ---------- build ----------

build: build-api build-ai build-web ## build all components

build-api:
	cd apps/api && go build ./...

build-ai:
	cd services/ai && $(AI_PY) -m compileall -q app

build-web:
	cd apps/web && npm run build

# ---------- lint ----------

lint: lint-api lint-ai lint-web

lint-api:
	cd apps/api && go vet ./...

lint-ai:
	cd services/ai && $(AI_PY) -m compileall -q app tests

lint-web:
	cd apps/web && npm run build

# ---------- test ----------

test: test-unit ## fast tests by default

test-unit: test-unit-api test-unit-ai test-unit-web

test-unit-api:
	cd apps/api && go test ./...

test-unit-ai:
	cd services/ai && $(AI_PY) -m pytest tests/unit -q

test-unit-web:
	cd apps/web && npm run build

test-integration: ## requires running services (make dev)
	cd apps/api && DATABASE_URL="$${DATABASE_URL:-postgres://workbench:workbench-dev-only@localhost:$${POSTGRES_PORT:-5432}/workbench?sslmode=disable}" go test -tags=integration ./tests/integration/... -count=1
	cd services/ai && $(AI_PY) -m pytest tests/integration -q


test-e2e:
	@echo "E2E: defined in tests/e2e — run after user flows exist"

test-security:
	@echo "security suite: tests/security — grows with features"

test-performance:
	@echo "performance suite: tests/performance — grows with features"

# ---------- data ----------

seed: ## load demo dataset
	docker compose exec -T postgres psql -U $${POSTGRES_USER:-workbench} -d $${POSTGRES_DB:-workbench} < scripts/seed.sql

clean:
	cd apps/api && go clean -testcache
	rm -rf apps/web/dist services/ai/**/__pycache__
	docker compose down -v 2>/dev/null || true
