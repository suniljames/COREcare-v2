# tools/v1-screenshot-catalog/

> **This tool produces input *for* v2 (the screenshot catalog committed to [`docs/legacy/v1-ui-catalog/`](../../docs/legacy/v1-ui-catalog/)). It does not run against v2 itself.** v1 is reached as a remote HTTP target via `V1_BASE_URL`. See [`docs/legacy/README.md`](../../docs/legacy/README.md) for what this tool's output is for.

One-shot Playwright crawler. ~250 LOC of plain TypeScript across three files (`crawl.ts`, `personas.config.ts`, `routes-allowlist.ts`). No abstractions, no plugin systems — runs once per refresh cycle and gets committed alongside its output.

## Read order

Before running anything in this directory:

1. [`INVESTIGATIONS.md`](INVESTIGATIONS.md) — what we know about v1 (personas, integrations, login flow)
2. [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md) — mandatory pre-crawl gate
3. [`CAPTION-STYLE.md`](CAPTION-STYLE.md) — for the human caption-authoring follow-up

## Bring-up runbook

The crawler assumes a v1 stack is already running. It does **not** start v1.

### 1. Pre-flight: v1 checked out, migrated, fixture loaded

```bash
cd ~/Code/COREcare-access
git fetch && git checkout 9738412a6e41064203fc253d9dd2a5c6a9c2e231

# Use SQLite (default) — single file, deterministic, no extra services
unset DATABASE_URL
python manage.py migrate

# Load the PHI-scrubbed fixture (must be authored before first run)
python manage.py loaddata fixtures/v2_catalog_snapshot.json
sha256sum fixtures/v2_catalog_snapshot.json
# Record this hash in docs/legacy/v1-ui-catalog/RUN-MANIFEST.md
```

> **Verification:** `python manage.py shell` → `from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.count())` should match the fixture's expected user count (typically 6 personas × 1+ users each).

### 2. Start v1 with outbound integrations disabled

v1 dev is integration-safe by default (per Phase 0 INVESTIGATIONS.md), but explicit flags make the runbook self-documenting:

```bash
TWILIO_DISABLED=1 SENDGRID_DISABLED=1 STRIPE_DISABLED=1 QUICKBOOKS_DISABLED=1 \
  python manage.py runserver 0.0.0.0:8000
```

> **Verification:** `curl -sf http://localhost:8000/dashboard/login/` returns 200 with the login form HTML.

### 3. Run the crawler

```bash
cd ~/Code/COREcare-v2/tools/v1-screenshot-catalog
cp .env.example .env
# Edit .env: fill in V1_*_USERNAME / V1_*_PASSWORD per persona that the
# fixture seeded. Leave any persona pair empty to skip its catalog section.

pnpm install
pnpm exec playwright install chromium
pnpm crawl --output-dir ../../docs/legacy/v1-ui-catalog/
```

The crawler runs five pre-flight gates, then crawls inventory rows persona-by-persona. Expect ~30 minutes for a full run against ~134 inventory rows × 2 viewports.

### 4. Reproducibility re-run

After step 3 completes, re-run the crawler against the same v1 commit + same fixture into a different output directory:

```bash
pnpm crawl --output-dir /tmp/catalog-rerun/
bash ../../scripts/check-catalog-reproducibility.sh \
  ../../docs/legacy/v1-ui-catalog/ \
  /tmp/catalog-rerun/
```

Expected: <0.5% per-image pixel diff (test T2 of #107's test spec). Larger diffs surface non-determinism that must be root-caused before merge.

### 5. PHI audit

```bash
# Manual audit per PHI-CHECKLIST.md verification methodology.
# 10% sample (cap 100), random.seed(42).
```

Commit the audit artifact (`PHI-AUDIT-<DATE>.md`) alongside the catalog.

## Pre-flight gates

`crawl.ts` runs five pre-flight checks before any auth attempt. All must pass:

1. `V1_BASE_URL` set and reachable (2-second `fetch` ping).
2. Production-hostname blocklist passed (literal regex array in `crawl.ts`, not env-driven).
3. All persona env vars set for at least one persona.
4. Output directory exists and is writable.
5. Inventory file (`docs/migration/v1-pages-inventory.md`) parses successfully via `scripts/extract-inventory-routes.sh`.

Each gate fails with an actionable error message + the remediation step.

## Network interception

The crawler sets up Playwright network interception that aborts every non-`GET` request unless its URL is on the explicit allowlist (login, role-switch). This is the second-line guard against destructive endpoints — the first line is v1's outbound-integration env disablement (#2 above).

`intercepted-non-GET.log` records every aborted request as the audit artifact for T4 (destructive-endpoint protection).

## Determinism harness

To make T2 (byte-identical re-run) achievable, `crawl.ts` injects a `page.addInitScript` block that:

- Replaces `Math.random()` with a seeded RNG (seed = sha256 of `v1_commit + canonical_id`)
- Mocks `Date.now()` and `new Date()` to the v1 commit's timestamp
- Disables CSS animations + transitions
- Disables image lazy-loading

Each item is documented in `crawl.ts` source comments — future maintainers will want to know why these are there.

## Output layout

```
<output-dir>/
├── RUN-MANIFEST.md                    # audit trail (timestamp, v1 SHA, fixture hash, route counts)
├── crawl.log                          # structured JSON log per route
├── crawl-bfs-report.md                # routes reachable but not in inventory (cross-check)
├── intercepted-non-GET.log            # security audit artifact
├── super-admin/
│   ├── 001-<route>.desktop.webp
│   ├── 001-<route>.mobile.webp
│   └── 001-<route>.md                 # frontmatter only; body TODO until Phase 3
├── agency-admin/
└── ... (per persona-slug)
```

Image files are committed via Git LFS per ADR-010. Captions, manifests, and logs stay in regular git.

## Boundary statement

This tool exists in v2 (`tools/v1-screenshot-catalog/` in `suniljames/COREcare-v2`) but operates against v1 (`hcunanan79/COREcare-access`). It does not modify v1. It does not require commit access to v1. The path `~/Code/COREcare-access/` in the runbook is the developer's local checkout — substitute any local path. The crawler only needs `V1_BASE_URL` to be reachable.

If `V1_BASE_URL` matches a known production hostname, the crawler hard-fails before any credential is sent. The blocklist is a literal regex array in `crawl.ts`, not env-driven (env can be tampered with).
