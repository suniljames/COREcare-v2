# ADR-006: Claude API for AI Features

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-001 (Architecture), ADR-007 (Audit)

## Context

COREcare v2 includes AI-powered features: conversational agent (SMS/WhatsApp), smart scheduling, anomaly detection, and visit summaries. We need a language model API that is capable, reliable, and safe for healthcare use.

## Decision

Use the **Claude API (Anthropic)** as the primary AI backend.

### Integration Pattern
- **Agent service** — centralized service in `api/app/services/ai.py` that manages all Claude API interactions
- **Prompt templates** — versioned templates stored in code, never user-editable
- **Safety guardrails:**
  - No PHI in prompts (substitute with anonymized placeholders)
  - System prompts enforce HIPAA-safe responses
  - Output validation before displaying to users
  - All AI interactions audit-logged
- **Cost management:** Token usage tracked per request, per tenant, with configurable limits
- **Fallback:** Graceful degradation when API is unavailable (features degrade, don't break)

## Consequences

### Positive
- State-of-the-art language model with strong safety training
- Excellent for structured data extraction and summarization
- Tool use capabilities for agentic workflows
- Anthropic's focus on AI safety aligns with healthcare use case

### Negative
- External API dependency with latency implications
- Cost per token (managed via caching and token budgets)
- Model behavior can change between versions
- Internet connectivity required for AI features

### Risks
- PHI leaking into prompts — mitigate with pre-processing pipeline that strips/anonymizes PHI
- Cost overruns — mitigate with per-tenant token budgets and caching
- Model hallucination in medical context — mitigate with output validation and human-in-the-loop for clinical decisions
