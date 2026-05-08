# Testing Guide

## Stack

| Layer | Tool | Location |
|-------|------|----------|
| API unit/service | pytest + pytest-asyncio | `api/app/tests/` |
| API integration | httpx + FastAPI TestClient | `api/app/tests/` |
| Web unit | vitest + @testing-library/react | `web/src/**/__tests__/` |
| E2E browser | Playwright | `web/e2e/` |

## TDD Workflow

Tests are written **before** feature code:

1. **RED** — Scaffold failing tests from the issue's Test Specification
2. **GREEN** — Write minimum code to make tests pass
3. **REFACTOR** — Clean up with tests as safety net

### Layer priority

1. **API service tests** (fastest, no HTTP) — always start here
2. **API endpoint tests** (httpx TestClient) — after service layer is green
3. **Web component tests** (vitest) — for React component behavior
4. **E2E tests** (Playwright) — last, for cross-page workflows

### Ad-hoc issues (no committee review)

Write 2-3 service-layer test cases based on the issue description:
- Happy path
- Primary error case
- Edge case mentioned in the issue

## Running Tests

```bash
# All tests
make test

# API only
make api-test

# Web only
make web-test

# E2E (requires Docker stack running)
make test-e2e

# Individual
cd api && uv run pytest -x -k "test_name"
cd web && pnpm test -- --filter "test_name"
```

## API Test Patterns

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_healthz(client: AsyncClient):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

## Web Test Patterns

```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MyComponent } from './MyComponent'

describe('MyComponent', () => {
  it('renders heading', () => {
    render(<MyComponent />)
    expect(screen.getByRole('heading')).toHaveTextContent('Expected')
  })
})
```

## E2E Test Patterns

```typescript
import { test, expect } from '@playwright/test'

test('caregiver sees dashboard', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
})
```

## Multi-Tenancy Testing

Every data-access service test must verify tenant isolation:
- Data created by Agency A is NOT visible to Agency B
- Super-admin can see data across all agencies
- RLS policies are enforced at the database level

## CI Architecture

```
Pull Requests:
  API Lint      — ruff + mypy
  API Tests     — pytest against PostgreSQL 16
  Web Lint      — eslint + prettier
  Web Typecheck — tsc --noEmit
  Web Tests     — vitest
  Web Build     — next build

Push to main (additionally):
  E2E Tests     — Playwright against full Docker stack
```

---

*v1 reference-doc validation conventions (sub-letter codes, MT meta-tests, awk authoring rules) live in [`docs/migration/doc-validation-conventions.md`](../migration/doc-validation-conventions.md). They govern the v1 reference docset, not v2 application tests.*
