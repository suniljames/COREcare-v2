# ADR-009: Multi-Agent Engineering Split

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-006 (Claude API)

## Context

A single AI model acting as both builder and validator creates correlated failure modes — shared blind spots, single-model groupthink, and no independent verification.

## Decision

Split engineering agent roles across two LLM backends: **Claude Code** (builder) and **Google Gemini** (validator).

The full rationale, role assignments, coordination protocol, and guiding principles are documented in the [engineering directives](https://github.com/suniljames/directives/blob/main/framework/agent-architecture.md).

## COREcare-Specific Implementation

- **Builder agent:** Claude Code — uses `/define`, `/design`, `/implement`, `/review`, `/summarize` commands
- **Validator agent:** Google Gemini CLI — uses equivalent commands per `GEMINI.md`
- **Coordination:** GitHub issues and PRs in this repo, label-driven handoff
- **Identity:** Both agents operate as `suniljames`

## Consequences

### Positive
- Independent validation catches blind spots a single model would miss
- Security and QA audits are genuinely independent
- Clear separation of concerns between building and validating

### Negative
- Two AI systems to configure and maintain
- Cross-model handoffs add coordination overhead
- Requires structured artifact schemas both models understand
