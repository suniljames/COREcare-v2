// crawl.ts — one-shot Playwright crawler that captures v1 (COREcare-access)
// UI as a per-persona screenshot catalog committed to docs/legacy/v1-ui-catalog/.
//
// READ tools/v1-screenshot-catalog/README.md FIRST. It documents the bring-up
// runbook and what each pre-flight gate is checking.
//
// This file is deliberately ~one screen of code per concern. No abstractions,
// no plugin systems — one-shot tooling.

import { chromium, type Browser, type BrowserContext, type Page } from "playwright";
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync, accessSync, constants as fsConstants } from "node:fs";
import { resolve, dirname } from "node:path";
import { createHash } from "node:crypto";
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
// Inventory parsing — shells out to the canonical bash extractor, parses JSON.
// ---------------------------------------------------------------------------

interface InventoryRow {
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
// Pre-flight gates — fail fast before any auth attempt.
// ---------------------------------------------------------------------------

interface PreflightArgs {
  v1BaseUrl: string;
  outputDir: string;
  repoRoot: string;
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
}

function fail(msg: string): never {
  console.error(`error: ${msg}`);
  process.exit(2);
}

// ---------------------------------------------------------------------------
// Determinism harness — encoded in page.addInitScript before any v1 page JS
// runs. Each item documented; future maintainers will want to know why.
// ---------------------------------------------------------------------------

function makeDeterminismScript(canonicalId: string, v1Commit: string): string {
  // Seeded RNG (mulberry32) — derived from sha256(v1_commit + canonical_id)
  // so every distinct route gets its own deterministic seed but the SAME
  // route across re-runs produces the same screenshots.
  const seedHex = createHash("sha256").update(v1Commit + canonicalId).digest("hex").slice(0, 8);
  const seed = parseInt(seedHex, 16);

  // The mocked timestamp is the v1 commit's tagger date. We don't actually
  // know it without `git log`, so we use a stable derived value: parseInt of
  // the first 8 chars of the SHA. Pages that show "now" or "today" will
  // render this constant, which is fine — they re-render the same value
  // every run.
  const fakeNow = parseInt(v1Commit.slice(0, 8), 16);

  return `
    (function() {
      // 1. Seeded RNG. Mulberry32 — small, deterministic.
      let s = ${seed};
      Math.random = function() {
        s = (s + 0x6D2B79F5) | 0;
        let t = s;
        t = Math.imul(t ^ (t >>> 15), 1 | t);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };

      // 2. Mock Date — only the constructor + Date.now. Other Date methods
      // delegate to the real implementation against the mocked instant.
      const RealDate = Date;
      const fixed = ${fakeNow};
      function MockDate(...args) {
        if (args.length === 0) return new RealDate(fixed);
        return new RealDate(...args);
      }
      MockDate.now = () => fixed;
      MockDate.parse = RealDate.parse;
      MockDate.UTC = RealDate.UTC;
      MockDate.prototype = RealDate.prototype;
      Date = MockDate;

      // 3. Disable CSS animations + transitions — prevents partially-animated
      // screenshots and removes a common source of pixel jitter on re-run.
      const style = document.createElement('style');
      style.textContent = '*, *::before, *::after { animation-duration: 0s !important; transition-duration: 0s !important; }';
      (document.head || document.documentElement).appendChild(style);

      // 4. Disable image lazy-loading — force every <img> to load
      // synchronously on the page so screenshots capture rendered images.
      document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('img[loading="lazy"]').forEach((el) => {
          el.loading = 'eager';
        });
      });
    })();
  `;
}

// ---------------------------------------------------------------------------
// Network interception — GET-only with explicit non-GET allowlist.
// ---------------------------------------------------------------------------

interface InterceptedRecord {
  method: string;
  url: string;
  origin: "page-script" | "navigation";
}

async function setupNetworkInterception(
  ctx: BrowserContext,
  v1BaseUrl: string,
  intercepted: InterceptedRecord[],
): Promise<void> {
  await ctx.route("**/*", (route) => {
    const req = route.request();
    const method = req.method();
    const url = req.url();

    // Block any URL matching the production hostname blocklist (defense in
    // depth — the pre-flight gate already caught V1_BASE_URL, but a page
    // script could still issue an outbound request to a blocked host).
    if (isBlockedHost(url) && !url.startsWith(v1BaseUrl)) {
      intercepted.push({ method, url, origin: "page-script" });
      route.abort();
      return;
    }

    if (method === "GET") {
      route.continue();
      return;
    }

    // Non-GET: must be on the allowlist
    const allowed = ALLOWED_NON_GET_FRAGMENTS.some((frag) => url.includes(frag));
    if (allowed) {
      route.continue();
      return;
    }

    intercepted.push({ method, url, origin: "page-script" });
    route.abort();
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
// Frontmatter writer.
// ---------------------------------------------------------------------------

interface CaptionFrontmatter {
  canonicalId: string;
  route: string;
  persona: string;       // canonical name
  viewport: "desktop" | "mobile";
  seedState: string;     // "populated" | "empty" | etc.
  v1Commit: string;
  generated: string;     // YYYY-MM-DD
}

export function renderCaption(fm: CaptionFrontmatter): string {
  return `---
canonical_id: ${fm.canonicalId}
route: ${fm.route}
persona: ${fm.persona}
viewport: ${fm.viewport}
seed_state: ${fm.seedState}
v1_commit: ${fm.v1Commit}
generated: ${fm.generated}
---
<!-- TODO: author CTAs + interaction notes per CAPTION-STYLE.md (Phase 3) -->
`;
}

// ---------------------------------------------------------------------------
// Single-route capture. Loads the URL, takes desktop + mobile screenshots,
// writes the frontmatter-only caption file.
// ---------------------------------------------------------------------------

interface CaptureArgs {
  ctx: BrowserContext;
  baseUrl: string;
  v1Commit: string;
  outputDir: string;
  persona: Persona;
  row: InventoryRow;
  index: number;        // sequence number within the persona section
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

  // Skip rows already in skip-reason state — the inventory pre-declares
  // them as not_screenshotted: <reason> for documented reasons.
  if (args.row.screenshot_ref.startsWith("not_screenshotted:")) {
    const reason = args.row.screenshot_ref.replace(/^not_screenshotted:\s*/, "");
    return { status: "skipped", reason, durationMs: Date.now() - start };
  }

  // Derive the route slug from the route path: take the last non-empty
  // segment (or "root" if path is /). Sequence number prefixed.
  const cleaned = args.row.route.replace(/^\/|\/$/g, "");
  const lastSeg = cleaned.split("/").filter((s) => !s.startsWith("<")).pop() || "root";
  const routeSlug = lastSeg.replace(/[^a-z0-9-]/gi, "-").toLowerCase();
  const seq = String(args.index).padStart(3, "0");
  const fileBase = `${seq}-${routeSlug}`;
  const canonicalId = `${args.persona.slug}/${fileBase}`;

  const personaDir = `${args.outputDir}/${args.persona.slug}`;
  mkdirSync(personaDir, { recursive: true });

  // Inject determinism harness for this route.
  await args.ctx.addInitScript({
    content: makeDeterminismScript(canonicalId, args.v1Commit),
  });

  const page = await args.ctx.newPage();
  page.setDefaultTimeout(args.perRouteTimeoutMs);

  try {
    const url = `${args.baseUrl}${args.row.route}`;
    await page.goto(url, { waitUntil: "networkidle" });

    // Capture both viewports as PNG, encode as WebP via sharp.
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

    // Write the frontmatter-only caption.
    const today = new Date().toISOString().slice(0, 10);
    const caption = renderCaption({
      canonicalId,
      route: args.row.route,
      persona: args.persona.canonical,
      viewport: "desktop",        // primary viewport (per #107 UX review)
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
// Main entry point.
// ---------------------------------------------------------------------------

interface CliArgs {
  outputDir: string;
}

function parseArgs(argv: string[]): CliArgs {
  const args: Partial<CliArgs> = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--output-dir") {
      args.outputDir = argv[++i];
    } else if (argv[i] === "--help" || argv[i] === "-h") {
      console.log("usage: pnpm crawl --output-dir <path>");
      process.exit(0);
    } else {
      console.error(`unknown arg: ${argv[i]}`);
      process.exit(2);
    }
  }
  if (!args.outputDir) {
    console.error("error: --output-dir is required");
    process.exit(2);
  }
  return args as CliArgs;
}

async function main(): Promise<void> {
  const cli = parseArgs(process.argv.slice(2));
  const v1BaseUrl = process.env.V1_BASE_URL || "http://localhost:8000";
  const v1Commit = process.env.V1_COMMIT_SHA || "9738412a6e41064203fc253d9dd2a5c6a9c2e231";
  const perRouteTimeoutMs = parseInt(process.env.CRAWL_PER_ROUTE_TIMEOUT_MS || "10000", 10);
  const repoRoot = resolve(dirname(import.meta.url.replace("file://", "")), "../..");
  const outputDir = resolve(cli.outputDir);

  await preflight({ v1BaseUrl, outputDir, repoRoot });

  const inventory = loadInventory(repoRoot);
  const intercepted: InterceptedRecord[] = [];

  const browser: Browser = await chromium.launch({ headless: true });
  const startTs = new Date().toISOString();

  let captured = 0;
  let skipped = 0;
  let errored = 0;

  try {
    for (const persona of ACTIVE_PERSONAS) {
      const ctx = await browser.newContext({
        viewport: { width: 1440, height: 900 },
      });
      await setupNetworkInterception(ctx, v1BaseUrl, intercepted);

      const page = await ctx.newPage();
      try {
        await login(page, v1BaseUrl, persona);
      } catch (e) {
        console.error(`login failed for ${persona.slug}: ${(e as Error).message}`);
        await ctx.close();
        continue;
      }
      await page.close();

      // Inventory rows + any allowlist routes that target this persona.
      // Allowlist routes get a synthetic screenshot_ref derived from the URL
      // so the capture loop treats them identically to inventory rows.
      const allowlistRows = ROUTES_ALLOWLIST.filter(
        (r) => r.persona === persona.canonical,
      ).map((r) => ({
        persona: r.persona,
        route: r.url,
        screenshot_ref: `${persona.slug}/allowlist-${r.url.replace(/[^a-z0-9]/gi, "-")}`,
      }));
      const personaRows = [
        ...inventory.filter((r) => r.persona === persona.canonical),
        ...allowlistRows,
      ];
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

        // structured log line per route
        console.log(
          JSON.stringify({
            event: `route.${result.status === "captured" ? "visited" : result.status}`,
            persona: persona.slug,
            route: row.route,
            canonical_id: result.canonicalId,
            reason: result.reason,
            duration_ms: result.durationMs,
          }),
        );
      }

      await ctx.close();
    }
  } finally {
    await browser.close();
  }

  const endTs = new Date().toISOString();

  // Write RUN-MANIFEST.md
  const manifest = [
    `# RUN-MANIFEST — v1 UI catalog crawl`,
    ``,
    `**Generated:** ${endTs}`,
    `**v1 commit:** ${v1Commit}`,
    `**v1 base URL:** ${v1BaseUrl}`,
    `**Started:** ${startTs}`,
    ``,
    `## Personas`,
    ``,
    `**Active:** ${ACTIVE_PERSONAS.map((p) => p.canonical).join(", ") || "(none)"}`,
    `**Skipped (no credentials):** ${SKIPPED_PERSONAS.map((p) => p.canonical).join(", ") || "(none)"}`,
    ``,
    `## Counts`,
    ``,
    `- Routes captured: ${captured}`,
    `- Routes skipped: ${skipped}`,
    `- Routes errored: ${errored}`,
    `- Non-GET requests intercepted: ${intercepted.length}`,
    ``,
    `## Inventory ↔ catalog parity`,
    ``,
    `Run \`bash scripts/check-v1-catalog-coverage.sh\` from the repo root to verify.`,
    ``,
  ].join("\n");
  writeFileSync(`${outputDir}/RUN-MANIFEST.md`, manifest);

  // Write intercepted-non-GET.log (T4 audit artifact)
  writeFileSync(
    `${outputDir}/intercepted-non-GET.log`,
    intercepted.map((r) => JSON.stringify(r)).join("\n") + "\n",
  );

  if (errored > 0) {
    console.error(`crawl finished with ${errored} errored routes`);
    process.exit(1);
  }
}

// Only run main() if invoked directly (not when imported by tests).
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
