# Test Budget Policy

## Principle

Every test should run at the **cheapest layer** that still validates the behavior.

## Test Layers

| Layer | Tool | When to Use | Speed |
|-------|------|-------------|-------|
| **API Service** | pytest | Pure logic, models, services | 1-10 ms |
| **API Endpoint** | httpx/TestClient | HTTP status, response shapes, auth | 10-50 ms |
| **Web Component** | vitest + RTL | Component rendering, user interaction | 10-100 ms |
| **E2E** | Playwright | Cross-page workflows, JS interaction, IDOR | 2-5 s |

## Decision Checklist

1. **Does the test verify business logic with no HTTP?** -> API Service
2. **Does the test check API response codes/shapes?** -> API Endpoint
3. **Does the test check React component behavior?** -> Web Component
4. **Does the test require a full browser (JS, navigation, viewport)?** -> E2E
5. **Does the test verify IDOR/auth boundaries?** -> E2E (marked `@security`)
6. **Does the test check mobile/responsive layout?** -> E2E

## Enforcement

- New E2E tests require justification (why can't this be a cheaper layer?)
- Layer decisions happen during committee review (QA Engineer assigns in Test Specification)
