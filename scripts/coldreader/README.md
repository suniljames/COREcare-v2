# Cold-reader rotation drift detector

A weekly CI job that asserts each persona section of `docs/migration/v1-pages-inventory.md` still answers its **cold-reader rotation** — the 3 contract questions a fresh AI agent must be able to answer from the section + cross-reference index alone.

Catches silent regressions where a future PR edits a row in a way that drops a load-bearing fact (e.g., the "linked-client only" clause in a Family Member row).

Originated in [issue #123](https://github.com/suniljames/COREcare-v2/issues/123); pattern source is the at-author-time cold-reader test in #103, #84, #85, etc.

## How it works

1. **Schedule:** Mon 06:00 UTC (`.github/workflows/v1-inventory-coldreader.yml`).
2. **Loop:** for each persona in the whitelist, extract the section + cross-reference index, send to Claude Haiku 4.5 with the 3 rotation questions.
3. **Score:** the model returns `{answer, verbatim_evidence, confidence}` via structured tool-use. The verifier asserts (a) every `verbatim_evidence` string literally appears in the section/index and (b) the answer's keywords overlap with the fixture's `expected_fact_summary` at ≥30%.
4. **Retry:** any failed question retries once with extended thinking. If still failing → real drift, run fails.
5. **Surface:** the run posts a step summary; on drift, opens or comments on a deduplicated tracking issue (`coldreader-drift` label). Auto-closes the issue when a subsequent run passes.

## Layout

```
scripts/coldreader/
  pyproject.toml           # uv-managed; anthropic + pyyaml pinned
  uv.lock                  # checked in
  run.py                   # CLI entry point
  inventory.py             # section + cross-ref-index parser
  fixtures.py              # YAML fixture loader + PHI deny
  verifier.py              # verbatim-evidence + soft-summary checks
  client.py                # Anthropic SDK wrapper + RotationCall/Response
  runner.py                # two-pass orchestration + tracking-issue rendering
  prompts/rotation.md      # system prompt template
  fixtures/<persona>.yaml  # 3 questions + expected_fact_summary per persona
  tests/                   # pytest L1+L2+L3
```

## Running locally

```bash
make coldreader-test          # pytest L1+L2+L3 (no API key)
make coldreader-local-dry     # parser + fixture validation against live inventory; no API call
make coldreader-local PERSONA=family-member   # live API call for one persona; requires ANTHROPIC_API_KEY
make coldreader-local         # all 7 personas
```

CLI flags:

| Flag                 | Meaning                                                            |
| -------------------- | ------------------------------------------------------------------ |
| `--dry-run`          | Parser + fixture validation only. No API call.                     |
| `--persona <slug>`   | Run only one persona. Whitelist: see below.                        |
| `--no-retry`         | Disable Pass-B extended-thinking retry.                            |
| `--inventory <path>` | Override inventory path (default: `docs/migration/v1-pages-inventory.md`). |

Exit codes: `0` PASS, `1` DRIFT, `2` setup/parser/cost-guardrail error.

## Persona whitelist

Defined in `inventory.py::PERSONAS`. New personas require BOTH a fixture file AND a whitelist edit; there is no auto-discovery.

```
agency-admin, super-admin, caregiver, care-manager, client, family-member, shared-routes
```

## Fixture schema

Each fixture file is `scripts/coldreader/fixtures/<persona>.yaml`:

```yaml
persona: family-member               # must match the filename
min_section_bytes: 3500              # floor for the section's body; ≥1000
questions:
  - id: q1                            # unique within the fixture
    text: "What does a Family Member see when they log into v1?"
    expected_fact_summary: |
      Family Members reach `/family/dashboard/` — a card per linked client...
  - id: q2
    text: "..."
    expected_fact_summary: |
      ...
  - id: q3
    text: "..."
    expected_fact_summary: |
      ...
```

Rules:

- Exactly 3 questions per fixture.
- `expected_fact_summary` is both a human-readable contract AND the soft-compare target during scoring. Write it as a multi-line description of the load-bearing facts the answer must mention. The verifier treats ≥30% keyword overlap as PASS.
- `min_section_bytes` must be ≥ 1000. Calibrate to ~70% of the section's current size — high enough to fail if a refactor halves the section, low enough to absorb minor edits.
- No PHI: real-looking emails, SSNs (`123-45-6789`), and DOBs (`03/15/1956` or `1956-03-15`) are rejected. Use the documented placeholder tokens (`[CLIENT_NAME]`, `<FAMILY_MEMBER>`, etc.) instead.

## When the drift issue opens

The auto-managed issue title is **`chore: v1 inventory cold-reader rotation drift detected`**, labeled `documentation` + `coldreader-drift`. The body links to the failing run; the run's step summary names the persona, question, and missing-evidence string.

Author runbook:

1. Open the failing run from the issue link; read the step summary.
2. For the named persona/question, open `docs/migration/v1-pages-inventory.md` to the section and re-read.
3. Decide:
   - **The section dropped a load-bearing fact** → re-author the row(s); re-run `make coldreader-local PERSONA=<slug>` locally to confirm the rotation passes; commit + PR.
   - **The question's contract changed** → edit `scripts/coldreader/fixtures/<persona>.yaml` to update the question or `expected_fact_summary`. Bump `min_section_bytes` only if the section is intentionally smaller now. Get reviewer sign-off — fixture changes are the contract.
4. After landing the fix, the next scheduled (or manually-dispatched via `Actions → V1 Inventory Cold-Reader Rotation → Run workflow`) run will auto-close the drift issue.

## Threat model

**Egress:** the runner sends only the persona section + cross-reference index (markdown content from `v1-pages-inventory.md`) to Anthropic's API. No PHI by construction — the inventory uses placeholder tokens for any client-identifying values, and the fixture loader's PHI-deny set rejects real-looking PHI in fixtures themselves.

**Authentication:** `ANTHROPIC_API_KEY` is a GitHub repository secret, scoped to this purpose, with a $5/month hard cap on the Anthropic side. Rotated annually. Never logged — the runner emits only token counts and structural metadata to step summaries.

**Prompt injection:** content inside `<inventory_section>` and `<cross_reference_index>` blocks is wrapped in delimiters; the system prompt explicitly instructs the model to treat their content as data, not instructions. Verbatim-evidence verification is the second line of defense — even a successful steer to "answer yes" requires producing literal evidence that survives substring validation.

**Supply chain:** dependencies (`anthropic`, `pyyaml`) are pinned in `pyproject.toml`; `uv.lock` is checked in; CI uses `uv sync --frozen`. The existing repo-level gitleaks scan covers `scripts/coldreader/**` and the workflow YAML.

## Cost guardrails

| Layer                | Bound                                                |
| -------------------- | ---------------------------------------------------- |
| Per-run input        | abort if uncached input tokens > 200,000             |
| Per-run output       | abort if output tokens > 30,000                      |
| Per-month spend      | $5 hard cap on the Anthropic API key                 |
| Workflow timeout     | `timeout-minutes: 10`                                |

Expected cost on Haiku 4.5 with prompt caching: ≈ $0.05 per run × 4 runs/month ≈ $0.20/month.

## Initial monitoring period

For the first 4 weekly runs after merge, review the step summary even on PASS — confirm the cache-hit ratio is ≥ 0.85 and total token counts match the projection. After that, only failures need attention.
