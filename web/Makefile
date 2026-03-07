# COREcare v2 Web
.PHONY: help lint typecheck test build dev

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run eslint + prettier
	pnpm lint

typecheck: ## Run TypeScript type checking
	pnpm typecheck

test: ## Run vitest
	pnpm test

test-e2e: ## Run Playwright E2E tests
	pnpm test:e2e

build: ## Build for production
	pnpm build

dev: ## Start dev server
	pnpm dev

format: ## Auto-format code
	pnpm lint:fix
