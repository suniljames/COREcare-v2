# COREcare v2 API
.PHONY: help lint test migrate seed dev

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run ruff + mypy
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy app/

format: ## Auto-format code
	uv run ruff check --fix .
	uv run ruff format .

test: ## Run pytest
	uv run pytest

test-cov: ## Run pytest with coverage
	uv run pytest --cov=app --cov-report=term-missing

migrate: ## Run Alembic migrations
	uv run alembic upgrade head

migration: ## Create a new Alembic migration
	uv run alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed test data
	uv run python -m app.seed

dev: ## Run dev server with reload
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
