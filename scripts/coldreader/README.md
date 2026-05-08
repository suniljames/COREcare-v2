# Cold-reader rotation drift detector

A weekly CI job that asserts each persona section of `docs/migration/v1-pages-inventory.md` still answers its **cold-reader rotation** — the 3 contract questions a fresh AI agent must be able to answer from the section + cross-reference index alone.

Catches silent regressions where a future PR edits a row in a way that drops a load-bearing fact (e.g., the "linked-client only" clause in a Family Member row).

Originated in [issue #123](https://github.com/suniljames/COREcare-v2/issues/123); pattern source is the at-author-time cold-reader test in #103, #84, #85, etc. Scoring rebuilt in [#163](https://github.com/suniljames/COREcare-v2/issues/163) to use explicit `must_mention` token lists rather than free-form prose keyword overlap.

## How it works

1. **Schedule:** Mon 06:00 UTC (`.github/workflows/v1-inventory-coldreader.yml`).
2. **Loop:** for each persona in the whitelist, extract the section + cross-reference index, send to Claude Haiku 4.5 with the 3 rotation questions.
3. **Score:** the model returns `{answer, verbatim_evidence, confidence}` via structured tool-use. The verifier asserts (a) every `verbatim_evidence` string literally appears in the section/index and (b) the answer contains every `must_mention` entry (within `tolerance` misses; case-insensitive substring; OR-groups for paraphrase tolerance).
4. **Retry:** any failed question retries once with extended thinking. If still failing → real drift, run fails.
5. **Surface:** the run posts a step summary including per-question hit counts (`q1: 5 of 5`, `q2: 4 of 5`); on drift, opens or comments on a deduplicated tracking issue (`coldreader-drift` label). Auto-closes the issue when a subsequent run passes. The model's self-reported `confidence` field is observation-only — it does NOT gate retry (the objective `must_mention` check is the gate). Passing answers that report `confidence=low` are surfaced as an aggregate `Low-confidence passes: N` line in the step summary plus per-question `WARNING coldreader.runner: low-confidence pass …` log lines on stderr (payload bounded to persona slug + question id + confidence enum value — never answer or evidence text). Values outside the `{high, low}` enum are coerced to `low` at the extractor (`client.py`), increment a separate `malformed_confidence_count`, and emit a per-question `WARNING coldreader.client: malformed confidence value: raw=… coerced=low` line on stderr (raw value escaped via `repr()` and capped at 64 chars to bound log-line length). A `Malformed confidence values: N` aggregate appears in the step summary when (and only when) `N > 0`. A non-zero count across consecutive runs indicates schema-vs-model drift (the model is emitting values the tool's input-schema enum doesn't allow) — pair with the matching log lines on stderr when triaging.

## Layout

```
scripts/coldreader/
  pyproject.toml           # uv-managed; anthropic + pyyaml pinned
  uv.lock                  # checked in
  run.py                   # CLI entry point
  inventory.py             # section + cross-ref-index parser
  fixtures.py              # YAML fixture loader + PHI deny + must_mention anchoring
  verifier.py              # verbatim-evidence + must_mention checks
  client.py                # Anthropic SDK wrapper + RotationCall/Response (captures text blocks)
  runner.py                # two-pass orchestration + telemetry + tracking-issue rendering
  prompts/rotation.md      # system prompt template
  fixtures/<persona>.yaml  # 3 questions + must_mention oracle per persona
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
| `--dry-run`          | Parser + fixture validation + must_mention anchoring. No API call. |
| `--persona <slug>`   | Run only one persona. Whitelist: see below.                        |
| `--no-retry`         | Disable Pass-B extended-thinking retry.                            |
| `--inventory <path>` | Override inventory path (default: `docs/migration/v1-pages-inventory.md`). |

Exit codes: `0` PASS, `1` DRIFT (content failure), `2` SETUP error (parser/anchoring/cost-guardrail/Pass-B tool refusal). **Setup errors dominate drift** — if any persona's questions hit a setup error, the runner exits `2` even when other personas have content drift, because system failures invalidate the calibration of the whole run.

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
    fact_summary: |
      Family Members reach `/family/dashboard/`...   # documentation only; not used by the validator
    must_mention:
      - ["/family/dashboard/", "family/dashboard"]   # OR-group: any one alternate satisfies the entry
      - ["ClientFamilyMember"]                        # single canonical form
      - ["linked-client"]
      - ["calendar"]
      - ["billing"]
    tolerance: 0                       # how many entries may be missing (default 0)
  - id: q2
    text: "..."
    fact_summary: |
      ...
    must_mention:
      - [...]
  - id: q3
    text: "..."
    fact_summary: |
      ...
    must_mention:
      - [...]
```

Rules:

- Exactly 3 questions per fixture.
- **`must_mention` is the validation oracle.** Each entry is an OR-group; the answer satisfies the entry if any alternate appears as a case-insensitive substring of the answer. Pick concrete identifiers (`is_superuser`, `billing_catalogs`, `/admin/view-as/kill-all/`, `@staff_member_required`, `phi_displayed`) over generic English words. 4–7 entries per question is typical.
- **Anchoring rule:** for every entry, at least one alternate MUST appear as a substring of the persona's section ∪ cross-reference index. The fixture loader and dry-run path enforce this; a stale token surfaces as `EXIT_SETUP_ERROR` before any API call.
- **`fact_summary`** is documentation only — guidance for fixture authors and human readers. It does NOT drive scoring. Write it as a multi-line description of the load-bearing facts the answer should cover, then derive `must_mention` from it.
- **Legacy `expected_fact_summary` key is rejected** at load — the rename is atomic.
- `tolerance` (default `0`) — how many `must_mention` entries the answer may miss without failing.
- `min_section_bytes` must be ≥ 1000. Calibrate to ~70% of the section's current size — high enough to fail if a refactor halves the section, low enough to absorb minor edits.
- **No PHI:** real-looking emails, SSNs (`123-45-6789`), and DOBs (`03/15/1956` or `1956-03-15`) are rejected — in `text`, `fact_summary`, AND every `must_mention` alternate. Use placeholder tokens (`[CLIENT_NAME]`, `<FAMILY_MEMBER>`, etc.) instead.

## Failure-message taxonomy

The runner classifies failures into two buckets:

| Class | Exit code | Meaning | What to do |
| --- | --- | --- | --- |
| `CONTENT` | `1` (DRIFT) | The model's answer is missing `must_mention` entries OR verbatim_evidence didn't match section/index | Inspect the failing question; the inventory may have lost a row, or the fixture is too strict |
| `SETUP` | `2` (SETUP) | Pass-B tool refusal (model emitted prose instead of tool call), unanchored `must_mention` token, parser error, or cost-guardrail trip | System-level issue: re-run; if persistent, inspect the captured text-block content (already truncated to 500 chars + PHI-scrubbed in the failure message) |

## When the drift issue opens

The auto-managed issue title is **`chore: v1 inventory cold-reader rotation drift detected`**, labeled `documentation` + `coldreader-drift`. The body links to the failing run; the run's step summary names the persona, question, and failure class.

### Author runbook

1. **Read the step summary.** Note each failing question's failure class (`CONTENT` vs `SETUP`) and the named missing entries.

2. **For `CONTENT` failures with missing `must_mention` entries:**
   - The model's answer was grounded but didn't mention the load-bearing token(s) the fixture demands. Two recoveries:
     - The inventory section legitimately changed (a row was renamed/dropped). Restore the row in `docs/migration/v1-pages-inventory.md` so the load-bearing fact is visible again.
     - The fixture is too strict — the missing token isn't truly load-bearing or the model now phrases it differently. Edit the fixture's `must_mention` to add an alternate form, or to remove the entry, with reviewer sign-off.
   - Re-run `make coldreader-local PERSONA=<slug>` locally to confirm the rotation passes; commit + PR.

3. **For `SETUP` failures:**
   - **Unanchored `must_mention` token at fixture load** → inventory drift caught early. The named token used to be in the section but isn't anymore. Restore the row, OR update the fixture to use a still-anchored alternate. Anchoring is enforced before any API call, so this never costs a model call.
   - **Pass-B tool refusal (text-block content surfaces in the failure message)** → the model declined to call the rotation tool under extended thinking. Usually transient; re-run the workflow once. If it recurs on the same question, the question may be too open-ended or the section may genuinely lack the fact — read the captured text-block prose for clues.
   - **Cost-guardrail trip** → uncached input or output tokens exceeded the per-run cap. The inventory or cross-reference index has grown; re-evaluate the cap or trim the section.

4. After landing the fix, the next scheduled (or manually-dispatched via `Actions → V1 Inventory Cold-Reader Rotation → Run workflow`) run will auto-close the drift issue.

## Threat model

**Egress:** the runner sends only the persona section + cross-reference index (markdown content from `v1-pages-inventory.md`) to Anthropic's API. No PHI by construction — the inventory uses placeholder tokens for any client-identifying values, and the fixture loader's PHI-deny set rejects real-looking PHI in fixtures themselves (in `text`, `fact_summary`, AND every `must_mention` alternate).

**Pass-B prose surface:** any text-block content captured from a Pass-B tool refusal is truncated to 500 chars and run through the same PHI-deny regex set before it lands in the failure message and the auto-issue body. Belt-and-suspenders; the model is grounded in non-PHI input.

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

For the first 4 weekly runs after merge, review the step summary even on PASS — confirm the cache-hit ratio is ≥ 0.85 and total token counts match the projection, and watch the per-question `must_mention` hit counts for trends (e.g., `5 of 5` slowly drifting to `4 of 5` on a particular question is an early signal of inventory or model-output drift). The `Low-confidence passes` count is a complementary signal: a sustained non-zero trend across consecutive runs indicates inventory ambiguity or model-quality regression even when the must_mention gate still passes — pair it with the matching `WARNING coldreader.runner: low-confidence pass …` log lines on stderr when triaging. A non-zero `Malformed confidence values` is a separate signal of schema-vs-model drift (the model emitted a value outside the `{high, low}` enum) even when the `must_mention` gate still passes. After that 4-week window, only failures need attention.
