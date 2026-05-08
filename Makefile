# COREcare v2 — Root Orchestrator
.PHONY: help up down build check test lint logs health

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Docker ---

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build all services
	docker compose build

logs: ## Tail logs for all services
	docker compose logs -f

health: ## Check health of all services
	@curl -sf http://localhost:8000/healthz && echo " API: OK" || echo " API: FAIL"
	@curl -sf http://localhost:3000 > /dev/null && echo " Web: OK" || echo " Web: FAIL"
	@docker compose exec db pg_isready -U corecare > /dev/null 2>&1 && echo " DB:  OK" || echo " DB:  FAIL"
	@docker compose exec redis redis-cli ping > /dev/null 2>&1 && echo " Redis: OK" || echo " Redis: FAIL"

# --- Quality Gates ---

check: ## Run all quality gates (pre-PR)
	$(MAKE) -C api lint
	$(MAKE) -C api test
	$(MAKE) -C web lint
	$(MAKE) -C web typecheck
	$(MAKE) -C web test
	$(MAKE) -C web build

# --- Individual targets ---

lint: ## Run all linters
	$(MAKE) -C api lint
	$(MAKE) -C web lint

test: ## Run all tests
	$(MAKE) -C api test
	$(MAKE) -C web test

test-e2e: ## Run Playwright E2E tests against full Docker stack
	$(MAKE) -C web test-e2e

# --- V1 reference docs ---

test-v1-docs: ## Run v1 doc hygiene + structure + catalog scripts self-tests
	bash scripts/tests/test_check_v1_doc_hygiene.sh
	bash scripts/tests/test_check_v1_doc_structure.sh
	bash scripts/tests/test_check_v1_catalog_coverage.sh
	bash scripts/tests/test_extract_inventory_routes.sh
	bash scripts/tests/test_post_v1_sha_bump_diff.sh

coldreader-test: ## Run coldreader pytest (L1+L2+L3, no API key needed)
	cd scripts/coldreader && uv sync --frozen && uv run --frozen pytest -q

coldreader-local-dry: ## Validate coldreader fixtures + parser against live inventory; no API call
	cd scripts/coldreader && uv sync --frozen && uv run --frozen python run.py --dry-run

coldreader-local: ## Run coldreader rotation (live API call); requires ANTHROPIC_API_KEY. Set PERSONA=<slug> to scope.
	cd scripts/coldreader && uv sync --frozen && uv run --frozen python run.py $(if $(PERSONA),--persona $(PERSONA))

scan-v1-docs: ## Run hygiene + structure + catalog-coverage scripts over committed docs
	@if compgen -G "docs/migration/v1-*.md" > /dev/null; then \
		bash scripts/check-v1-doc-hygiene.sh docs/migration/v1-*.md; \
	else \
		echo "No v1 reference docs to scan."; \
	fi
	@if [ -f docs/migration/v1-pages-inventory.md ] && [ -f docs/migration/v1-functionality-delta.md ]; then \
		bash scripts/check-v1-doc-structure.sh; \
	else \
		echo "Pages inventory or delta doc absent — structure check skipped."; \
	fi
	@if [ -f docs/migration/v1-pages-inventory.md ]; then \
		bash scripts/check-v1-catalog-coverage.sh; \
	else \
		echo "Pages inventory absent — catalog-coverage check skipped."; \
	fi

# --- API shortcuts ---

api-lint: ## Lint API
	$(MAKE) -C api lint

api-test: ## Test API
	$(MAKE) -C api test

api-migrate: ## Run Alembic migrations
	$(MAKE) -C api migrate

api-seed: ## Seed test data
	$(MAKE) -C api seed

# --- Web shortcuts ---

web-lint: ## Lint Web
	$(MAKE) -C web lint

web-test: ## Test Web
	$(MAKE) -C web test

web-build: ## Build Web
	$(MAKE) -C web build

web-typecheck: ## Typecheck Web
	$(MAKE) -C web typecheck

# --- Database ---

db-reset: ## Reset database (drop + recreate + migrate + seed)
	docker compose exec db dropdb -U corecare --if-exists corecare
	docker compose exec db createdb -U corecare corecare
	$(MAKE) api-migrate
	$(MAKE) api-seed
