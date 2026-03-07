# ADR-001: FastAPI + Next.js Architecture

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-004 (SQLModel), ADR-008 (shadcn/ui)

## Context

COREcare v1 is a Django monolith with server-rendered templates. While functional, this architecture limits us in several ways:

- **No real-time capabilities** without bolting on Django Channels
- **Tight coupling** between UI and business logic
- **Mobile experience** is constrained by server-rendered HTML
- **API-first design** is difficult to retrofit onto a template-based app
- **Performance** suffers from synchronous request handling

COREcare v2 needs to serve multiple frontends (web, PWA, future native apps), support real-time features (messaging, notifications), and scale to multiple agencies.

## Decision

Split into two services:

1. **FastAPI (Python 3.12)** — async-first API backend
   - Native async/await for database, HTTP, and WebSocket operations
   - Pydantic for request/response validation
   - OpenAPI schema auto-generation
   - Dependency injection for auth, tenant context, database sessions
   - Python ecosystem preserved (team familiarity, library compatibility)

2. **Next.js 15 (App Router)** — React-based frontend
   - Server Components for fast initial loads and SEO
   - Client Components for interactive features
   - App Router for layout composition and streaming
   - PWA support for mobile installation
   - TypeScript for type safety across the frontend

## Consequences

### Positive
- Clean API-first design enables future mobile apps and third-party integrations
- Async FastAPI handles concurrent requests efficiently (important for real-time features)
- Next.js SSR/SSG gives excellent page load performance
- Independent deployment of frontend and backend
- Strong type safety: Pydantic (backend) + TypeScript (frontend)

### Negative
- Two codebases to maintain (vs one Django app)
- Development requires running two services (mitigated by Docker Compose)
- Schema synchronization between backend and frontend (mitigated by OpenAPI codegen)
- Team needs proficiency in both Python and TypeScript

### Risks
- Frontend-backend contract drift — mitigate with OpenAPI schema validation in CI
- Increased operational complexity — mitigate with Docker Compose and unified Makefile
