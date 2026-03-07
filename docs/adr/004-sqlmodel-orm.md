# ADR-004: SQLModel for ORM

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-001 (Architecture), ADR-002 (RLS)

## Context

FastAPI uses Pydantic for data validation. SQLAlchemy is the standard Python ORM. SQLModel bridges both — models are simultaneously SQLAlchemy tables and Pydantic schemas.

Options:
1. **Raw SQLAlchemy 2.0** — most mature, most flexible, most verbose
2. **SQLModel** — SQLAlchemy + Pydantic fusion by the FastAPI creator
3. **Tortoise ORM** — async-first, less mature ecosystem
4. **SQLAlchemy + separate Pydantic models** — explicit separation, more boilerplate

## Decision

Use **SQLModel** as the primary ORM with escape hatches to raw SQLAlchemy when needed.

- Models define both database schema and API serialization
- Async sessions via SQLAlchemy's async engine
- Alembic for migrations (using SQLAlchemy metadata under the hood)
- For complex queries or features not yet supported by SQLModel, drop to SQLAlchemy directly

## Consequences

### Positive
- Single model definition for DB + API (less boilerplate)
- Type safety with Pydantic validation
- Created by the same author as FastAPI — tight integration
- SQLAlchemy 2.0 under the hood — battle-tested query engine

### Negative
- SQLModel relationship support has gaps (especially for complex joins)
- Smaller community than raw SQLAlchemy
- Some SQLAlchemy patterns require workarounds
- Async support requires careful session management

### Risks
- SQLModel limitations blocking a feature — mitigate by using raw SQLAlchemy for complex queries
- Version compatibility — pin SQLModel and SQLAlchemy versions together
