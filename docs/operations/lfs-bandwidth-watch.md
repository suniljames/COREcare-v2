# Runbook — Git LFS bandwidth watch (post-#107)

## Why this exists

The v1 UI screenshot catalog committed in [#107](https://github.com/suniljames/COREcare-v2/issues/107) ships 168 WebP files via Git LFS. [ADR-010](../adr/010-v1-ui-catalog-storage.md) names GitHub LFS bandwidth quota as a foreseeable constraint and reserves Alternative B (separate static site / `gh-pages` branch / new repo) as the escalation path. [Issue #185](https://github.com/suniljames/COREcare-v2/issues/185) is the 30-day operational watch period that confirms or refutes the constraint and decides whether to escalate.

This runbook is the operator-facing companion to that issue. Follow it weekly through 2026-06-07.

## What happens automatically

Per [#233](https://github.com/suniljames/COREcare-v2/issues/233), most of the watch ritual is mechanized:

- A bot posts a check-in comment on issue #185 every Saturday at 17:00 UTC (10:00 PT) during the watch window. Each check-in includes the reset-day caveat below as a one-line reminder.
- A bot posts a day-30 closure prompt on 2026-06-07 walking the operator through the closure steps.
- When the operator posts a comment matching the closure-template signature (anchored on `^**30-day Git LFS bandwidth report**`), an auto-closure PR opens within 60 seconds deleting both watch workflows and closing #185 via `Closes #185`. Idempotent — duplicate matches do not produce duplicate PRs.
- If the report comment also contains "Red flag" or "ADR-010 follow-up", an escalation issue is auto-filed using `.github/ISSUE_TEMPLATE/lfs-bandwidth-escalation.md` and the new issue number appears in the closure PR body.

**The bandwidth read itself stays manual** — no automation touches the meter. If any automation step fails, the manual sections below remain the documented fallback.

## How to read the meter

GitHub does not expose per-repo Git LFS bandwidth via API for personal accounts. The Settings → Billing → "Git LFS Data" web panel is the only authoritative source. Read it manually.

1. Open [`https://github.com/settings/billing`](https://github.com/settings/billing).
2. Scroll to the **Git LFS Data** section.
3. Record three numbers and one date:
   - **Bandwidth used this period** (MB)
   - **Bandwidth quota** (MB; expect 1024 MB / 1 GB on free tier)
   - **Reset date** for the current billing period
4. Take a screenshot of the Git LFS Data panel. Save it locally — it is the audit trail attached to every yellow-flag, red-flag, or closure comment.

The helper `scripts/lfs-bandwidth-snapshot.sh` prints these instructions plus a copy-paste day-30 closure template. It does not call the network.

## Decision tree

After every weekly read, evaluate the numbers in this order. Stop at the first match.

### Trigger A — single CI run > 100 MB LFS bandwidth

If a single workflow run consumed more than 100 MB of LFS bandwidth, find the workflow:

1. Open [`https://github.com/suniljames/COREcare-v2/actions`](https://github.com/suniljames/COREcare-v2/actions) and inspect the recent run with the spike.
2. Confirm the offending step is `actions/checkout` with `lfs: true` (explicit or implicit).
3. PR a fix that either sets `lfs: false` or adds `# rationale: <text>` per the convention enforced by `scripts/check-workflow-lfs-posture.sh`.
4. Stay in #185 — the fix lives in this issue's PR series, not a follow-up.

### Trigger B — cumulative monthly > 500 MB (yellow flag)

Post a yellow-flag comment on issue #185 using the template below. This is an early warning, not an escalation. Continue weekly reads.

### Trigger C — cumulative monthly > 800 MB OR trending to exceed 1 GB

Escalate per [ADR-010](../adr/010-v1-ui-catalog-storage.md) Alternative B. Post the red-flag comment on issue #185 using the template below, then file a follow-up implementation issue that evaluates three options:

- **(a)** Move the catalog to a `gh-pages` branch in this repo with LFS removed from the new branch
- **(b)** Move the catalog to a new repo `coreacare-v1-catalog/` with its own LFS quota
- **(c)** Build the catalog as a static-site artifact (Vercel / Netlify) and remove from this repo

The follow-up issue picks one. This runbook does not.

### None of the above

Log the reading locally (date + bandwidth + quota + reset day). No action required. Move on.

## Templates

### Yellow-flag comment

```markdown
**Yellow flag — Git LFS bandwidth crossed 50% of free-tier quota**

**Reading taken on:** YYYY-MM-DD
**Bandwidth used (account-wide):** XXX MB / 1024 MB (XX%)
**Reset day:** YYYY-MM-DD
**Largest single CI run since last reading:** XX MB (workflow: NAME)

No escalation yet — continuing weekly reads. Will reassess at next reading or if Trigger C threshold is crossed.

_Screenshot of Settings → Billing → Git LFS Data attached below._
```

### Red-flag comment

```markdown
**Red flag — Git LFS bandwidth on track to exceed free-tier quota**

**Reading taken on:** YYYY-MM-DD
**Bandwidth used (account-wide):** XXX MB / 1024 MB (XX%)
**Reset day:** YYYY-MM-DD
**Trend:** projected to exceed 1 GB before reset

Escalating per ADR-010 Alternative B. Filing follow-up issue to evaluate (a) `gh-pages` branch / (b) new repo / (c) static-site artifact.

Follow-up issue: _link_

_Screenshot of Settings → Billing → Git LFS Data attached below._
```

### Day-30 closure comment

Run `scripts/lfs-bandwidth-snapshot.sh` to print this template pre-filled with today's date and the issue's static fields. Edit the TBDs and post.

```markdown
**30-day Git LFS bandwidth report** for [`docs/legacy/v1-ui-catalog/`](https://github.com/suniljames/COREcare-v2/tree/main/docs/legacy/v1-ui-catalog) (post-#107 merge).

**Period:** 2026-05-07 → 2026-06-07
**Reading taken on:** YYYY-MM-DD
**Bandwidth used (account-wide):** _TBD_ MB / 1024 MB free-tier quota
**Largest single CI run observed:** _TBD_ MB (workflow: _TBD_)
**Reset day(s) within window:** _TBD_

_Screenshot of Settings → Billing → Git LFS Data attached below._

**Outcome:** [Threshold not approached → closing as resolved.] *or* [Yellow flag triggered on _date_; mitigation _link_.] *or* [Red flag → ADR-010 follow-up filed at _link_.]
```

## Reset-day caveat

GitHub's LFS bandwidth meter resets on the account's billing-period reset day (typically the account creation anniversary). If the reset day falls **inside** the 30-day watch window for #185, report bandwidth from both sides of the reset:

```
**Bandwidth used:** XXX MB this period (since YYYY-MM-DD reset) + YYY MB previous period (YYYY-MM-DD to YYYY-MM-DD)
```

Do not sum the two periods into a single "30-day total" — the quota is per-period, and the trend that matters for escalation is the within-period rate, not the cross-reset cumulative.

## Cleanup after closure

When #185 closes, delete `.github/workflows/lfs-bandwidth-day30-reminder.yml` in the closure PR. The cron is one-shot and serves no purpose after the day-30 report is posted.

## Related

- [ADR-010 — v1 UI Screenshot Catalog Storage](../adr/010-v1-ui-catalog-storage.md)
- [Issue #107 — Phase 2 catalog merge](https://github.com/suniljames/COREcare-v2/issues/107)
- [Issue #185 — this watch period](https://github.com/suniljames/COREcare-v2/issues/185)
- [`scripts/check-workflow-lfs-posture.sh`](../../scripts/check-workflow-lfs-posture.sh)
- [`scripts/lfs-bandwidth-snapshot.sh`](../../scripts/lfs-bandwidth-snapshot.sh)
