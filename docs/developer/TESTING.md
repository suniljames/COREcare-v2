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

## Doc-structure validation conventions

The bash + awk validators in `scripts/check-v1-doc-structure.sh` (and its sibling
`scripts/check-v1-doc-hygiene.sh`) emit violation codes — short two-letter-prefix
identifiers like `SL-1a`, `EL-2b`, `RR-4c` — that the test suite at
`scripts/tests/test_check_v1_doc_structure.sh` exercises one at a time via fixture
directories. The convention has been hardened over several issues; the rules below
are the post-#196 final form.

### 1. Sub-letter when ≥2 emit branches share a code

Any code with two or more `print FILENAME ":" FNR ": <CODE>: ..."` emit branches
is **sub-lettered** at the awk emit site (`SL-1a`, `SL-1b`, `SL-3a / SL-3b / SL-3c`,
`EL-2a / EL-2b`, `CR-1a / CR-1b`, `GL-3a / GL-3b / GL-3c`, `RR-4a..d`). Single-emit
codes (`SL-2`, `SL-4`, `EL-1`, `WF-1`, etc.) stay bare.

Canonical reference shape: `^[A-Z]{2}-[0-9]+[a-z]?$`. At most one trailing
sub-letter. No dots, no underscores, no multi-letter suffixes.

### 2. Fixtures use `assert_exit_and_match` with shortest-unique substrings

Every sub-lettered code's negative fixture asserts both the exit code AND a
substring of the emit message that distinguishes its branch from siblings:

```bash
assert_exit_and_match "SL-3b: severity empty when v2_status=missing fails" 1 \
  'SL-3b:.*severity is empty' \
  "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-empty"
```

Bare `assert_exit` is forbidden for any sub-lettered code. Rationale: an exit-1
from any other branch would silently pass an exit-only fixture. Positive
fixtures (expecting exit 0) need no substring; their description token still
uses the sub-letter so MT-1 sees the branch as covered.

### 3. MT-1 enforces per-branch parity

The meta-test at `scripts/tests/test_check_v1_doc_structure.sh:2685+` asserts
that the set of distinct code references in the awk equals the set of fixture
description tokens. The umbrella filter `_filter_umbrellas` drops bare `X-N`
when `X-N<letter>` is also present, so umbrella mentions in headers and prose
comments don't pollute parity.

A fixture for every emit branch — not just every code — is required.

### 4. MT-2 enforces canonical code shape

A second meta-test at `scripts/tests/test_check_v1_doc_structure.sh:3055+`
greps the structure script for any code-shaped reference and fails if any
match doesn't conform to `^[A-Z]{2}-[0-9]+[a-z]?$`. Hard trip-wire on drift
forms `SL-1.1`, `SL_1a`, `SL-1ab` — they would otherwise silently disappear
from MT-1's set.

### 5. Authoring inside the integrations awk block

The awk script in `scripts/check-v1-doc-structure.sh` is enclosed in BASH
single quotes. Inside the awk block, **literal `'` characters in comments or
strings break the bash quoting** and surface as `awk: syntax error` at
runtime. To include an apostrophe in an awk string, use the escape `'\''`
(see existing emit lines for the pattern). For comments, rephrase without
apostrophes.

### Where the rule lives

The authoritative convention comment is at `scripts/tests/test_check_v1_doc_structure.sh:577`.
This section is a navigational pointer for new contributors; the comment in
the test file is the source of truth.
