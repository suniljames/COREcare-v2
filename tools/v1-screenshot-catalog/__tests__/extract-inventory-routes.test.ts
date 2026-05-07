import { describe, it, expect, beforeAll } from "vitest";
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve, join } from "node:path";

// Tests the canonical inventory parser at scripts/extract-inventory-routes.sh.
// This is the single source of truth shared between PR-A's coverage script
// and PR-C's crawler — drift here breaks both.

const REPO_ROOT = resolve(__dirname, "..", "..", "..");
const SCRIPT = join(REPO_ROOT, "scripts", "extract-inventory-routes.sh");

function runScript(inventoryPath: string): unknown {
  const out = execFileSync("bash", [SCRIPT, "--inventory", inventoryPath]);
  return JSON.parse(out.toString("utf-8"));
}

describe("extract-inventory-routes.sh", () => {
  beforeAll(() => {
    if (!existsSync(SCRIPT)) {
      throw new Error(`script not found: ${SCRIPT}`);
    }
  });

  // Inventory row schema (matches docs/migration/v1-pages-inventory.md):
  //   | route | purpose | what_user_sees | v2_status | severity | mt | rls | phi | screenshot_ref | v2_link |
  // Awk -F"|" sees 12 fields total (10 columns + leading + trailing empty).

  it("emits a JSON array on stdout", () => {
    const dir = mkdtempSync(join(tmpdir(), "inv-test-"));
    const fixture = join(dir, "inv.md");
    writeFileSync(fixture, [
      "## Super-Admin",
      "",
      "| route | purpose | what | v2 | sev | mt | rls | phi | screenshot_ref | v2_link |",
      "|-------|---------|------|----|-----|----|----|-----|----------------|---------|",
      "| `/admin/dashboard/` | x | x | x | x | x | x | x | super-admin/001-dashboard |  |",
      "| `/admin/clients/` | x | x | x | x | x | x | x | not_screenshotted: pending #79 |  |",
      "",
    ].join("\n"));
    const rows = runScript(fixture) as Array<{ persona: string; route: string; screenshot_ref: string }>;
    expect(Array.isArray(rows)).toBe(true);
    expect(rows).toHaveLength(2);
  });

  it("captures persona, route, screenshot_ref columns correctly", () => {
    const dir = mkdtempSync(join(tmpdir(), "inv-test-"));
    const fixture = join(dir, "inv.md");
    writeFileSync(fixture, [
      "## Caregiver",
      "",
      "| route | purpose | what | v2 | sev | mt | rls | phi | screenshot_ref | v2_link |",
      "|-------|---------|------|----|-----|----|----|-----|----------------|---------|",
      "| `/caregiver/today/` | x | x | x | x | x | x | x | caregiver/001-today |  |",
      "",
    ].join("\n"));
    const rows = runScript(fixture) as Array<{ persona: string; route: string; screenshot_ref: string }>;
    expect(rows[0]).toEqual({
      persona: "Caregiver",
      route: "/caregiver/today/",
      screenshot_ref: "caregiver/001-today",
    });
  });

  it("ignores rows outside a locked-persona H2 section", () => {
    const dir = mkdtempSync(join(tmpdir(), "inv-test-"));
    const fixture = join(dir, "inv.md");
    writeFileSync(fixture, [
      "## Random Section",
      "",
      "| route | purpose | what | v2 | sev | mt | rls | phi | screenshot_ref | v2_link |",
      "|-------|---------|------|----|-----|----|----|-----|----------------|---------|",
      "| `/random/` | x | x | x | x | x | x | x | random-ref |  |",
      "",
    ].join("\n"));
    const rows = runScript(fixture) as unknown[];
    expect(rows).toHaveLength(0);
  });

  it("ignores rows that don't have a backtick-slash route (excludes summary tables)", () => {
    const dir = mkdtempSync(join(tmpdir(), "inv-test-"));
    const fixture = join(dir, "inv.md");
    writeFileSync(fixture, [
      "## Super-Admin",
      "",
      "| route | purpose | what | v2 | sev | mt | rls | phi | screenshot_ref | v2_link |",
      "|-------|---------|------|----|-----|----|----|-----|----------------|---------|",
      "| `/admin/dashboard/` | x | x | x | x | x | x | x | super-admin/001 |  |",
      "| total | summary | x | x | x | x | x | x | x |  |",
      "",
    ].join("\n"));
    const rows = runScript(fixture) as unknown[];
    expect(rows).toHaveLength(1);
  });

  it("handles all six locked persona names", () => {
    const dir = mkdtempSync(join(tmpdir(), "inv-test-"));
    const fixture = join(dir, "inv.md");
    const sections = ["Super-Admin", "Agency Admin", "Care Manager", "Caregiver", "Client", "Family Member"]
      .map((name, i) => [
        `## ${name}`,
        "",
        "| route | purpose | what | v2 | sev | mt | rls | phi | screenshot_ref | v2_link |",
        "|-------|---------|------|----|-----|----|----|-----|----------------|---------|",
        `| \`/route-${i}/\` | x | x | x | x | x | x | x | ref-${i} |  |`,
        "",
      ].join("\n"))
      .join("\n");
    writeFileSync(fixture, sections);
    const rows = runScript(fixture) as Array<{ persona: string }>;
    expect(rows).toHaveLength(6);
    const personas = rows.map((r) => r.persona).sort();
    expect(personas).toEqual([
      "Agency Admin",
      "Care Manager",
      "Caregiver",
      "Client",
      "Family Member",
      "Super-Admin",
    ]);
  });

  it("exits with code 2 on missing inventory file", () => {
    let caught: unknown = null;
    try {
      execFileSync("bash", [SCRIPT, "--inventory", "/nonexistent/path.md"], { stdio: "pipe" });
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeTruthy();
    expect((caught as { status?: number }).status).toBe(2);
  });
});
