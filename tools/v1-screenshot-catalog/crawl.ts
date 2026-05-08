// crawl.ts — one-shot Playwright crawler that captures v1 (COREcare-access)
// UI as a per-persona screenshot catalog committed to docs/legacy/v1-ui-catalog/.
//
// READ tools/v1-screenshot-catalog/README.md FIRST. It documents the bring-up
// runbook and what each pre-flight gate is checking.
//
// This file is deliberately ~one screen of code per concern. No abstractions,
// no plugin systems — one-shot tooling.
//
// Worker concurrency is intentionally NOT exposed. With ~134 inventory rows × 2
// viewports = ~270 page loads × 2.5s avg, single-worker runtime is ~11 min on
// a developer's Mac. Adding workers buys little and adds 4× v1 connection load.

import { chromium, type Browser, type BrowserContext, type Page } from "playwright";
import { execFileSync } from "node:child_process";
import {
  mkdirSync,
  writeFileSync,
  readFileSync,
  existsSync,
  accessSync,
  constants as fsConstants,
  createWriteStream,
  type WriteStream,
} from "node:fs";
import { resolve, dirname } from "node:path";
import { createHash } from "node:crypto";
import { hostname, platform } from "node:os";
import sharp from "sharp";
import { ACTIVE_PERSONAS, SKIPPED_PERSONAS, type Persona } from "./personas.config.ts";
import { ROUTES_ALLOWLIST, ALLOWED_NON_GET_FRAGMENTS } from "./routes-allowlist.ts";

// ---------------------------------------------------------------------------
// Production-hostname blocklist (literal regexes, not env-driven — env can be
// tampered with). T11 of #107.
// ---------------------------------------------------------------------------
export const BLOCKED_HOSTS: RegExp[] = [
  /\.elitecare\..+/i,
  /bayareaelitehomecare\.com/i,
  /corecare\.app/i,
];

export function isBlockedHost(url: string): boolean {
  return BLOCKED_HOSTS.some((re) => re.test(url));
}

// ---------------------------------------------------------------------------
// Network-interception predicate. Pure function so we can unit-test it
// without spinning up Playwright. T4 of #107 reduces to "what does this
// return for each (method, url, v1BaseUrl) input?"
// ---------------------------------------------------------------------------

export interface AllowDecision {
  allow: boolean;
  reason?: "blocked-host" | "non-get-not-allowlisted";
  allowedByFragment?: string;
}

export function shouldAllowRequest(input: {
  method: string;
  url: string;
  v1BaseUrl: string;
}): AllowDecision {
  // Defense-in-depth: production-hostname block runs first. Even a GET to a
  // production URL is aborted (a malicious page-script could try this).
  if (isBlockedHost(input.url) && !input.url.startsWith(input.v1BaseUrl)) {
    return { allow: false, reason: "blocked-host" };
  }
  if (input.method === "GET") {
    return { allow: true };
  }
  // Non-GET: must match an allowlist fragment.
  const matched = ALLOWED_NON_GET_FRAGMENTS.find((frag) => input.url.includes(frag));
  if (matched) {
    return { allow: true, allowedByFragment: matched };
  }
  return { allow: false, reason: "non-get-not-allowlisted" };
}

// ---------------------------------------------------------------------------
// Inventory parsing — shells out to the canonical bash extractor, parses JSON.
// ---------------------------------------------------------------------------

export interface InventoryRow {
  persona: string;
  route: string;
  screenshot_ref: string;
}

function loadInventory(repoRoot: string): InventoryRow[] {
  const out = execFileSync("bash", [
    `${repoRoot}/scripts/extract-inventory-routes.sh`,
    "--inventory",
    `${repoRoot}/docs/migration/v1-pages-inventory.md`,
  ]);
  return JSON.parse(out.toString("utf-8"));
}

// ---------------------------------------------------------------------------
// CLI args. Parser is a pure function so tests can drive it without spawning
// a process. exitOnError=false makes the parser throw instead of exit — used
// by tests to assert error messages.
// ---------------------------------------------------------------------------

export interface CliArgs {
  outputDir: string;
  resumeFrom?: string;
  onlyPersonas?: string[];
  onlyRoutes?: string[];
}

interface ParseOpts {
  exitOnError?: boolean;
}

export function parseArgs(argv: string[], opts: ParseOpts = { exitOnError: true }): CliArgs {
  const args: Partial<CliArgs> = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--output-dir") {
      args.outputDir = argv[++i];
    } else if (argv[i] === "--resume-from") {
      args.resumeFrom = argv[++i];
    } else if (argv[i] === "--only-personas") {
      args.onlyPersonas = argv[++i]
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
    } else if (argv[i] === "--only-routes") {
      args.onlyRoutes = argv[++i]
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
    } else if (argv[i] === "--help" || argv[i] === "-h") {
      console.log(
        "usage: pnpm crawl --output-dir <path> [--resume-from <slug>] [--only-personas a,b] [--only-routes id,id]",
      );
      process.exit(0);
    } else {
      const msg = `unknown arg: ${argv[i]}`;
      if (opts.exitOnError) {
        console.error(msg);
        process.exit(2);
      }
      throw new Error(msg);
    }
  }
  if (!args.outputDir) {
    const msg = "--output-dir is required";
    if (opts.exitOnError) {
      console.error(`error: ${msg}`);
      process.exit(2);
    }
    throw new Error(msg);
  }
  return args as CliArgs;
}

// ---------------------------------------------------------------------------
// Lead-viewport policy. Caregivers and family members work primarily from
// phones in the field (per docs/design-system/RESPONSIVE.md); their catalog
// captions lead with the mobile WebP. Other personas lead desktop.
// ---------------------------------------------------------------------------

export function leadViewportFor(personaSlug: string): "desktop" | "mobile" {
  return personaSlug === "caregiver" || personaSlug === "family-member"
    ? "mobile"
    : "desktop";
}

// ---------------------------------------------------------------------------
// Route → slug derivation. Shared by captureRoute (which uses it to compose
// the canonical_id) and applyRouteFilter (which uses it to match operator-
// supplied canonical_ids against inventory rows).
// ---------------------------------------------------------------------------

export function deriveRouteSlug(route: string): string {
  const cleaned = route.replace(/^\/|\/$/g, "");
  const lastSeg = cleaned.split("/").filter((s) => !s.startsWith("<")).pop() || "root";
  return lastSeg.replace(/[^a-z0-9-]/gi, "-").toLowerCase();
}

// ---------------------------------------------------------------------------
// URL-pattern placeholder substitution. v1's inventory rows use Django
// URL-pattern syntax (`<int:client_id>`, `<int:user_id>`, etc.). Django won't
// match a literal `<...>` in the URL, so the crawler must substitute concrete
// IDs from the seed fixture before issuing the GET.
//
// SEED_IDS is the in-code mapping of placeholder name → fixture-pk. Update
// here when the v2_catalog_snapshot.json fixture's pks change.
// ---------------------------------------------------------------------------

export const SEED_IDS: Record<string, number> = {
  "int:client_id": 1,        // clients.client.pk = 1
  "int:user_id": 4,          // auth.user.pk = 4 (caregiver)
  "int:caregiver_id": 4,     // same caregiver user
  "int:pk": 1,               // generic int — Care Manager cm_client_focus uses this for client pk (#237)
  "int:expense_id": 1,       // expenses.expense.pk = 1 (#237 fixture extension)
  "int:receipt_id": 1,       // expenses.expensereceipt.pk = 1 (#237 fixture extension)
  "id": 1,                   // generic int (default to client)
};

export interface SubstitutionResult {
  url: string;
  substituted: boolean;       // true if all placeholders resolved
  missing: string[];          // unresolved placeholder names
}

// Inventory `screenshot_ref` cells are the source of truth for whether a
// row should be captured or skipped. The taxonomy of skip-reasons lives in
// docs/legacy/README.md "Skip-reason taxonomy" — see issue #237 for the
// non_html_response application to cm_serve_receipt.
export type ScreenshotRefClassification =
  | { kind: "capture" }
  | { kind: "skip"; reason: string };

export function classifyScreenshotRef(ref: string): ScreenshotRefClassification {
  if (ref.startsWith("not_screenshotted:")) {
    const reason = ref.replace(/^not_screenshotted:\s*/, "").trim();
    return { kind: "skip", reason };
  }
  return { kind: "capture" };
}

export function substitutePlaceholders(
  route: string,
  ids: Record<string, number> = SEED_IDS,
): SubstitutionResult {
  // Match <name> where name doesn't contain `<` or `>`. Preserves <> empty
  // patterns by requiring at least one character.
  const placeholderRe = /<([^<>]+)>/g;
  const found = Array.from(route.matchAll(placeholderRe)).map((m) => m[1]);
  const missing: string[] = [];
  let url = route;
  for (const name of found) {
    const id = ids[name];
    if (id !== undefined) {
      url = url.replace(`<${name}>`, String(id));
    } else if (!missing.includes(name)) {
      missing.push(name);
    }
  }
  return {
    url,
    substituted: found.length > 0 && missing.length === 0,
    missing,
  };
}

// ---------------------------------------------------------------------------
// Retry-with-backoff. Used to wrap page.goto + screenshot calls in
// captureRoute. Only TimeoutError is retried; other errors propagate
// immediately. Schedule: 1s, 3s, 9s (each = baseMs × 3^attempt).
// ---------------------------------------------------------------------------

interface RetryOpts {
  attempts: number;
  baseMs: number;
  sleep?: (ms: number) => Promise<void>;
}

const defaultSleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

export async function retryWithBackoff<T>(fn: () => Promise<T>, opts: RetryOpts): Promise<T> {
  const sleep = opts.sleep ?? defaultSleep;
  let lastErr: unknown;
  for (let i = 0; i < opts.attempts; i++) {
    try {
      return await fn();
    } catch (e) {
      lastErr = e;
      if (!(e instanceof Error) || e.name !== "TimeoutError") {
        throw e;
      }
      if (i < opts.attempts - 1) {
        await sleep(opts.baseMs * Math.pow(3, i));
      }
    }
  }
  throw lastErr;
}

// ---------------------------------------------------------------------------
// Pre-flight gates — fail fast before any auth attempt.
// ---------------------------------------------------------------------------

interface PreflightArgs {
  v1BaseUrl: string;
  outputDir: string;
  repoRoot: string;
  fixtureHash: string;
}

async function preflight(args: PreflightArgs): Promise<void> {
  // Gate 1: V1_BASE_URL set + reachable
  if (!args.v1BaseUrl) {
    fail("Gate 1 failed: V1_BASE_URL is not set. Add it to .env.");
  }
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 2_000);
    const res = await fetch(args.v1BaseUrl, { signal: ctrl.signal });
    clearTimeout(t);
    if (res.status >= 500) {
      fail(`Gate 1 failed: v1 at ${args.v1BaseUrl} returned ${res.status}.`);
    }
  } catch (e) {
    fail(
      `Gate 1 failed: cannot reach v1 at ${args.v1BaseUrl}. Is \`python manage.py runserver\` running? (${(e as Error).message})`,
    );
  }

  // Gate 2: production-hostname blocklist
  if (isBlockedHost(args.v1BaseUrl)) {
    fail(
      `Gate 2 failed: V1_BASE_URL=${args.v1BaseUrl} matches the production blocklist. The crawler refuses to run against production.`,
    );
  }

  // Gate 3: at least one persona has both username + password
  if (ACTIVE_PERSONAS.length === 0) {
    fail(
      "Gate 3 failed: no personas have V1_*_USERNAME and V1_*_PASSWORD set in .env. Set credentials for at least one persona.",
    );
  }

  // Gate 4: output dir exists + writable
  if (!existsSync(args.outputDir)) {
    fail(`Gate 4 failed: --output-dir ${args.outputDir} does not exist. mkdir it first.`);
  }
  try {
    accessSync(args.outputDir, fsConstants.W_OK);
  } catch {
    fail(`Gate 4 failed: --output-dir ${args.outputDir} is not writable.`);
  }

  // Gate 5: inventory parses
  try {
    const rows = loadInventory(args.repoRoot);
    if (!Array.isArray(rows)) throw new Error("inventory output was not an array");
    if (rows.length === 0) {
      fail(
        "Gate 5 failed: inventory parsed to zero rows. Either the inventory file is empty or the parser is broken.",
      );
    }
  } catch (e) {
    fail(`Gate 5 failed: inventory parse failed (${(e as Error).message}).`);
  }

  // Gate 6: fixture sha256 present. The reproducibility-hash equality gate
  // (scripts/check-catalog-reproducibility.sh) is a security control — without
  // a real value, two runs both record `<unset>` and the gate produces a
  // false-positive match. The audit trail in RUN-MANIFEST.md also requires it.
  if (!args.fixtureHash || args.fixtureHash === "<unset>") {
    fail(
      "Gate 6 failed: V1_FIXTURE_SHA256 is not set. Compute `shasum -a 256 ~/Code/COREcare-access/fixtures/v2_catalog_snapshot.json` and export V1_FIXTURE_SHA256=<hash> before re-running.",
    );
  }
}

function fail(msg: string): never {
  console.error(`error: ${msg}`);
  process.exit(2);
}

// ---------------------------------------------------------------------------
// Determinism harness — encoded as a single addInitScript registered ONCE per
// BrowserContext (Phase 2A fix: the prior version registered per-route which
// accumulated stacked overrides on every page load).
// ---------------------------------------------------------------------------

function makeDeterminismScript(personaSlug: string, v1Commit: string): string {
  // Seed derived from sha256(v1_commit + persona_slug). Same persona's pages
  // share an RNG seed; same input across re-runs produces the same output.
  const seedHex = createHash("sha256").update(v1Commit + personaSlug).digest("hex").slice(0, 8);
  const seed = parseInt(seedHex, 16);
  // Mocked timestamp: parseInt of v1 SHA's first 8 chars. Stable across runs.
  const fakeNow = parseInt(v1Commit.slice(0, 8), 16);

  return `
    (function() {
      // 1. Seeded RNG (mulberry32). Replaces Math.random for any v1 page
      //    JS that uses it; same seed → same sequence across re-runs.
      let s = ${seed};
      Math.random = function() {
        s = (s + 0x6D2B79F5) | 0;
        let t = s;
        t = Math.imul(t ^ (t >>> 15), 1 | t);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };

      // 2. Mock Date constructor + Date.now to a fixed instant. Pages that
      //    show "now" or "today" render this constant value every run.
      const RealDate = Date;
      const fixed = ${fakeNow};
      function MockDate(...args) {
        if (!(this instanceof MockDate)) return new RealDate(fixed).toString();
        if (args.length === 0) return new RealDate(fixed);
        return new RealDate(...args);
      }
      MockDate.now = () => fixed;
      MockDate.parse = RealDate.parse;
      MockDate.UTC = RealDate.UTC;
      Date = MockDate;

      // 3. Disable CSS animations + transitions — kills a major source of
      //    pixel jitter on re-run.
      const style = document.createElement('style');
      style.textContent = '*, *::before, *::after { animation-duration: 0s !important; transition-duration: 0s !important; }';
      (document.head || document.documentElement).appendChild(style);

      // 4. Disable image lazy-loading so screenshots capture rendered images.
      document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('img[loading="lazy"]').forEach((el) => {
          el.loading = 'eager';
        });
      });
    })();
  `;
}

// ---------------------------------------------------------------------------
// Network interception — applies shouldAllowRequest's decision; logs
// non-allowed requests to the intercepted-non-GET.log audit artifact.
// ---------------------------------------------------------------------------

interface InterceptedRecord {
  method: string;
  url: string;
  origin: "page-script" | "navigation";
  reason: string;
}

async function setupNetworkInterception(
  ctx: BrowserContext,
  v1BaseUrl: string,
  intercepted: InterceptedRecord[],
): Promise<void> {
  await ctx.route("**/*", (route) => {
    const req = route.request();
    const decision = shouldAllowRequest({
      method: req.method(),
      url: req.url(),
      v1BaseUrl,
    });
    if (!decision.allow) {
      // Distinguishing navigation from page-script lets the runbook's
      // "STOP if any has origin: navigation" check have teeth — a captured
      // page that triggers a non-GET navigation is an inventory or
      // allowlist bug, not a beacon.
      intercepted.push({
        method: req.method(),
        url: req.url(),
        origin: req.isNavigationRequest() ? "navigation" : "page-script",
        reason: decision.reason ?? "unknown",
      });
      route.abort();
      return;
    }
    route.continue();
  });
}

// ---------------------------------------------------------------------------
// Persona login. Django session auth — POST to /dashboard/login/ via the
// browser form so CSRF + cookies just work.
// ---------------------------------------------------------------------------

async function login(page: Page, baseUrl: string, persona: Persona): Promise<void> {
  if (!persona.username || !persona.password) {
    throw new Error(`persona ${persona.slug} has no credentials`);
  }
  await page.goto(`${baseUrl}/dashboard/login/`, { waitUntil: "domcontentloaded" });
  await page.fill('input[name="username"]', persona.username);
  await page.fill('input[name="password"]', persona.password);
  await Promise.all([
    page.waitForLoadState("domcontentloaded"),
    page.click('button[type="submit"], input[type="submit"]'),
  ]);
}

// ---------------------------------------------------------------------------
// Frontmatter writer. Phase 2A renamed `viewport` → `lead_viewport`; each
// caption describes BOTH viewport WebPs of its route. lead_viewport encodes
// which viewport is canonical for the persona.
// ---------------------------------------------------------------------------

export interface CaptionFrontmatter {
  canonicalId: string;
  route: string;
  persona: string;       // canonical name
  leadViewport: "desktop" | "mobile";
  seedState: string;     // "populated" | "empty" | etc.
  v1Commit: string;
  generated: string;     // YYYY-MM-DD
}

export function renderCaption(fm: CaptionFrontmatter): string {
  return `---
canonical_id: ${fm.canonicalId}
route: ${fm.route}
persona: ${fm.persona}
lead_viewport: ${fm.leadViewport}
seed_state: ${fm.seedState}
v1_commit: ${fm.v1Commit}
generated: ${fm.generated}
---
<!-- TODO: author CTAs + interaction notes per CAPTION-STYLE.md (Phase 3) -->
`;
}

// ---------------------------------------------------------------------------
// RUN-MANIFEST.md writer. Pure function — operator/host/playwright_version
// are passed in so tests don't depend on `os` calls.
// ---------------------------------------------------------------------------

export interface ManifestArgs {
  v1BaseUrl: string;
  v1Commit: string;
  fixtureHash: string;
  activeCanonicals: readonly string[];
  skippedCanonicals: readonly string[];
  captured: number;
  skipped: number;
  errored: number;
  intercepted: number;
  startTs: string;
  endTs: string;
  operator: string;
  host: string;
  playwrightVersion: string;
}

export function renderManifest(a: ManifestArgs): string {
  const active = a.activeCanonicals.length > 0 ? a.activeCanonicals.join(", ") : "(none)";
  const skipped = a.skippedCanonicals.length > 0 ? a.skippedCanonicals.join(", ") : "(none)";
  return [
    `# RUN-MANIFEST — v1 UI catalog crawl`,
    ``,
    `This manifest documents the authoritative run that produced the catalog`,
    `committed alongside it. Re-runs against the same v1 commit + same fixture`,
    `should produce byte-identical output (within \`pixelmatch\` tolerance per`,
    `\`scripts/check-catalog-reproducibility.sh\`). If they don't, examine the`,
    `determinism harness in \`tools/v1-screenshot-catalog/crawl.ts\`.`,
    ``,
    `**Generated:** ${a.endTs}`,
    `**Started:** ${a.startTs}`,
    `**v1 commit:** ${a.v1Commit}`,
    `**v1 base URL:** ${a.v1BaseUrl}`,
    `**Fixture sha256:** ${a.fixtureHash}`,
    `**Operator:** ${a.operator}`,
    `**Host:** ${a.host}`,
    `**Playwright version:** ${a.playwrightVersion}`,
    ``,
    `## Personas`,
    ``,
    `**Active:** ${active}`,
    `**Skipped (no credentials):** ${skipped}`,
    ``,
    `## Counts`,
    ``,
    `- Routes captured: ${a.captured}`,
    `- Routes skipped: ${a.skipped}`,
    `- Routes errored: ${a.errored}`,
    `- Non-GET requests intercepted: ${a.intercepted}`,
    ``,
    `## Inventory ↔ catalog parity`,
    ``,
    `Run \`bash scripts/check-v1-catalog-coverage.sh\` from the repo root to verify.`,
    ``,
  ].join("\n");
}

// ---------------------------------------------------------------------------
// Structured-log emitter. Tees JSON-per-line to stdout AND <output-dir>/crawl.log.
// ---------------------------------------------------------------------------

interface Logger {
  emit: (event: Record<string, unknown>) => void;
  close: () => Promise<void>;
}

function makeLogger(filepath: string, append: boolean): Logger {
  const stream: WriteStream = createWriteStream(filepath, { flags: append ? "a" : "w" });
  return {
    emit(event) {
      const line = JSON.stringify(event);
      console.log(line);
      stream.write(line + "\n");
    },
    close() {
      // Resolve only after the WriteStream's "finish" event — guarantees the
      // file is flushed before main() may call process.exit(1).
      return new Promise<void>((resolve, reject) => {
        stream.end(() => resolve());
        stream.on("error", reject);
      });
    },
  };
}

// ---------------------------------------------------------------------------
// Single-route capture. Loads the URL, takes desktop + mobile screenshots,
// writes the frontmatter-only caption file. page.goto + screenshots wrapped
// in retryWithBackoff against TimeoutError.
// ---------------------------------------------------------------------------

interface CaptureArgs {
  ctx: BrowserContext;
  baseUrl: string;
  v1Commit: string;
  outputDir: string;
  persona: Persona;
  row: InventoryRow;
  index: number;
  perRouteTimeoutMs: number;
}

interface CaptureResult {
  status: "captured" | "skipped" | "errored";
  canonicalId?: string;
  reason?: string;
  durationMs: number;
}

async function captureRoute(args: CaptureArgs): Promise<CaptureResult> {
  const start = Date.now();

  const classified = classifyScreenshotRef(args.row.screenshot_ref);
  if (classified.kind === "skip") {
    return { status: "skipped", reason: classified.reason, durationMs: Date.now() - start };
  }

  // Substitute Django URL-pattern placeholders. Routes whose placeholders
  // can't be resolved from SEED_IDS skip with no_seed_data — the operator
  // can extend the fixture (and SEED_IDS) in a future refresh cycle.
  const sub = substitutePlaceholders(args.row.route);
  if (sub.missing.length > 0) {
    return {
      status: "skipped",
      reason: `no_seed_data (missing: ${sub.missing.join(", ")})`,
      durationMs: Date.now() - start,
    };
  }
  const concreteRoute = sub.url;

  const routeSlug = deriveRouteSlug(args.row.route);
  const seq = String(args.index).padStart(3, "0");
  const fileBase = `${seq}-${routeSlug}`;
  const canonicalId = `${args.persona.slug}/${fileBase}`;

  const personaDir = `${args.outputDir}/${args.persona.slug}`;
  mkdirSync(personaDir, { recursive: true });

  const page = await args.ctx.newPage();
  page.setDefaultTimeout(args.perRouteTimeoutMs);

  try {
    await retryWithBackoff(
      async () => {
        const url = `${args.baseUrl}${concreteRoute}`;
        await page.goto(url, { waitUntil: "networkidle" });

        for (const [viewport, dims] of [
          ["desktop", { width: 1440, height: 900 }],
          ["mobile",  { width: 390,  height: 844 }],
        ] as const) {
          await page.setViewportSize(dims);
          await page.waitForLoadState("networkidle");
          const png = await page.screenshot({ fullPage: true, type: "png" });
          const webp = await sharp(png).webp({ quality: 80 }).toBuffer();
          writeFileSync(`${personaDir}/${fileBase}.${viewport}.webp`, webp);
        }
      },
      { attempts: 3, baseMs: 1000 },
    );

    const today = new Date().toISOString().slice(0, 10);
    const caption = renderCaption({
      canonicalId,
      route: args.row.route,
      persona: args.persona.canonical,
      leadViewport: leadViewportFor(args.persona.slug),
      seedState: "populated",
      v1Commit: args.v1Commit,
      generated: today,
    });
    writeFileSync(`${personaDir}/${fileBase}.md`, caption);

    return { status: "captured", canonicalId, durationMs: Date.now() - start };
  } catch (e) {
    return {
      status: "errored",
      canonicalId,
      reason: (e as Error).message,
      durationMs: Date.now() - start,
    };
  } finally {
    await page.close();
  }
}

// ---------------------------------------------------------------------------
// Resume / filter logic for the per-persona loop. Pure exported functions —
// covered by __tests__/filters.test.ts. Indices are reassigned per-filtered-
// row in the main loop, so the operator's <persona>/NNN-slug input matches
// only by the slug part (the NNN- prefix is stripped before comparison).
// ---------------------------------------------------------------------------

export function applyPersonaFilters(
  personas: readonly Persona[],
  cli: CliArgs,
): Persona[] {
  let result: Persona[] = [...personas];
  if (cli.onlyPersonas) {
    const set = new Set(cli.onlyPersonas);
    result = result.filter((p) => set.has(p.slug));
  }
  if (cli.resumeFrom) {
    const i = result.findIndex((p) => p.slug === cli.resumeFrom);
    if (i >= 0) result = result.slice(i);
  }
  return result;
}

export function applyRouteFilter(
  rows: readonly InventoryRow[],
  personaSlug: string,
  cli: CliArgs,
): InventoryRow[] {
  if (!cli.onlyRoutes) return [...rows];
  // For each canonical_id targeted at this persona, extract the slug part
  // (strip the optional NNN- prefix). The set of allowed slugs is what we
  // match against each row's deriveRouteSlug(route).
  const allowedSlugs = new Set(
    cli.onlyRoutes
      .filter((id) => id.startsWith(`${personaSlug}/`))
      .map((id) => id.substring(personaSlug.length + 1).replace(/^\d+-/, "")),
  );
  if (allowedSlugs.size === 0) return [];
  return rows.filter((r) => allowedSlugs.has(deriveRouteSlug(r.route)));
}

// ---------------------------------------------------------------------------
// Main entry point.
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const cli = parseArgs(process.argv.slice(2));
  const v1BaseUrl = process.env.V1_BASE_URL || "http://localhost:8000";
  const v1Commit = process.env.V1_COMMIT_SHA || "9738412a6e41064203fc253d9dd2a5c6a9c2e231";
  const fixtureHash = process.env.V1_FIXTURE_SHA256 || "<unset>";
  const operator = process.env.GITHUB_USER || process.env.USER || "<unknown>";
  const perRouteTimeoutMs = parseInt(process.env.CRAWL_PER_ROUTE_TIMEOUT_MS || "10000", 10);
  const repoRoot = resolve(dirname(import.meta.url.replace("file://", "")), "../..");
  const outputDir = resolve(cli.outputDir);

  await preflight({ v1BaseUrl, outputDir, repoRoot, fixtureHash });

  const inventory = loadInventory(repoRoot);
  const intercepted: InterceptedRecord[] = [];
  // Append to crawl.log when resuming so we don't clobber the prior run's
  // events; truncate on a fresh run.
  const log = makeLogger(`${outputDir}/crawl.log`, !!cli.resumeFrom);

  const personasToRun = applyPersonaFilters(ACTIVE_PERSONAS, cli);

  log.emit({ event: "preflight.passed", v1_base_url: v1BaseUrl });

  const browser: Browser = await chromium.launch({ headless: true });
  const startTs = new Date().toISOString();

  let captured = 0;
  let skipped = 0;
  let errored = 0;

  try {
    for (const persona of personasToRun) {
      const ctx = await browser.newContext({
        viewport: { width: 1440, height: 900 },
      });
      // Determinism harness — registered ONCE per BrowserContext (Phase 2A
      // bug fix; the prior version registered per-route which accumulated
      // overrides on every page load).
      await ctx.addInitScript({
        content: makeDeterminismScript(persona.slug, v1Commit),
      });
      await setupNetworkInterception(ctx, v1BaseUrl, intercepted);

      const page = await ctx.newPage();
      try {
        await login(page, v1BaseUrl, persona);
        log.emit({ event: "persona.login", persona: persona.slug, status: "success" });
      } catch (e) {
        log.emit({
          event: "persona.login",
          persona: persona.slug,
          status: "failed",
          error: (e as Error).message,
        });
        await ctx.close();
        continue;
      }
      await page.close();

      const allowlistRows = ROUTES_ALLOWLIST.filter(
        (r) => r.persona === persona.canonical,
      ).map((r) => ({
        persona: r.persona,
        route: r.url,
        screenshot_ref: `${persona.slug}/allowlist-${r.url.replace(/[^a-z0-9]/gi, "-")}`,
      }));
      const personaRows = applyRouteFilter(
        [
          ...inventory.filter((r) => r.persona === persona.canonical),
          ...allowlistRows,
        ],
        persona.slug,
        cli,
      );
      let index = 0;
      for (const row of personaRows) {
        index++;
        const result = await captureRoute({
          ctx,
          baseUrl: v1BaseUrl,
          v1Commit,
          outputDir,
          persona,
          row,
          index,
          perRouteTimeoutMs,
        });

        if (result.status === "captured") captured++;
        else if (result.status === "skipped") skipped++;
        else errored++;

        log.emit({
          event: `route.${result.status === "captured" ? "visited" : result.status}`,
          persona: persona.slug,
          route: row.route,
          canonical_id: result.canonicalId,
          reason: result.reason,
          duration_ms: result.durationMs,
        });
      }

      await ctx.close();
    }
  } finally {
    await browser.close();
  }

  const endTs = new Date().toISOString();

  // Resolve playwright version for the manifest by reading its installed
  // package.json. readFileSync works on every Node version (no import-attribute
  // syntax dependency); fallbacks to "unknown" only when the file is missing.
  let playwrightVersion = "unknown";
  try {
    const pwPkgPath = `${repoRoot}/tools/v1-screenshot-catalog/node_modules/playwright/package.json`;
    const pwPkg = JSON.parse(readFileSync(pwPkgPath, "utf-8")) as { version?: string };
    playwrightVersion = pwPkg.version ?? "unknown";
  } catch {
    /* keep "unknown" */
  }

  const manifest = renderManifest({
    v1BaseUrl,
    v1Commit,
    fixtureHash,
    activeCanonicals: personasToRun.map((p) => p.canonical),
    skippedCanonicals: SKIPPED_PERSONAS.map((p) => p.canonical),
    captured,
    skipped,
    errored,
    intercepted: intercepted.length,
    startTs,
    endTs,
    operator,
    host: `${platform()} ${hostname()}`,
    playwrightVersion,
  });
  writeFileSync(`${outputDir}/RUN-MANIFEST.md`, manifest);

  const interceptedBody = intercepted.length > 0
    ? intercepted.map((r) => JSON.stringify(r)).join("\n") + "\n"
    : "";
  writeFileSync(`${outputDir}/intercepted-non-GET.log`, interceptedBody);

  log.emit({
    event: "run.complete",
    duration_ms: new Date(endTs).getTime() - new Date(startTs).getTime(),
    routes_visited: captured,
    routes_skipped: skipped,
    routes_errored: errored,
    fixture_hash: fixtureHash,
    playwright_version: playwrightVersion,
  });
  // Await flush so the run.complete event is durably on disk before any
  // exit. Without this, process.exit(1) below could race the WriteStream's
  // "finish" event and lose the most-grep'd line of crawl.log.
  await log.close();

  if (errored > 0) {
    console.error(`crawl finished with ${errored} errored routes`);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
