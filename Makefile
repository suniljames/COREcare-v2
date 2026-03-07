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
