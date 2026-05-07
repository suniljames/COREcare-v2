// Compares two v1-UI-catalog directories and emits a per-image pixel-diff
// report. T2 of #107: byte-identical (AA-jitter only) re-run.
//
// Replaces the prior bash-orchestrated `npx --yes` per-image variant which
// re-resolved every package on every invocation (300+ npx calls for a full
// catalog comparison). This in-process variant uses sharp (already installed
// as a runtime dep) + pixelmatch + pngjs from devDependencies.
//
// Usage:
//   pnpm tsx check-reproducibility.ts <baseline-dir> <rerun-dir>
//     [--threshold-pct N]   default 0.5 (percent of pixels allowed to differ)
//     [--output-dir <path>] default <rerun-dir>/reproducibility-report
//
// Exit codes:
//   0  every image is within threshold AND fixture hashes match
//   1  one or more images exceed threshold OR fixture hashes diverge
//   2  bad invocation

import { readdirSync, readFileSync, mkdirSync, writeFileSync, statSync, existsSync } from "node:fs";
import { join, relative } from "node:path";
import sharp from "sharp";
// pixelmatch 7.x ships its own types; pngjs types come from @types/pngjs.
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";

interface CliArgs {
  baseline: string;
  rerun: string;
  thresholdPct: number;
  outputDir: string;
}

function parseArgs(argv: string[]): CliArgs {
  const args: Partial<CliArgs> = { thresholdPct: 0.5 };
  const positional: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--threshold-pct") {
      args.thresholdPct = parseFloat(argv[++i]);
    } else if (argv[i] === "--output-dir") {
      args.outputDir = argv[++i];
    } else if (argv[i] === "-h" || argv[i] === "--help") {
      console.log(
        "usage: pnpm tsx check-reproducibility.ts <baseline-dir> <rerun-dir> [--threshold-pct N] [--output-dir <path>]",
      );
      process.exit(0);
    } else if (argv[i].startsWith("--")) {
      console.error(`unknown flag: ${argv[i]}`);
      process.exit(2);
    } else {
      positional.push(argv[i]);
    }
  }
  if (positional.length !== 2) {
    console.error("error: must pass two positional args: <baseline-dir> <rerun-dir>");
    process.exit(2);
  }
  args.baseline = positional[0];
  args.rerun = positional[1];
  args.outputDir ??= `${args.rerun}/reproducibility-report`;
  return args as CliArgs;
}

function findWebPs(root: string): string[] {
  const out: string[] = [];
  const walk = (dir: string) => {
    if (!existsSync(dir)) return;
    for (const name of readdirSync(dir)) {
      const path = join(dir, name);
      const st = statSync(path);
      if (st.isDirectory()) walk(path);
      else if (st.isFile() && name.endsWith(".webp")) out.push(path);
    }
  };
  walk(root);
  return out;
}

async function decodePng(filepath: string): Promise<PNG> {
  const png = await sharp(filepath).png().toBuffer();
  return PNG.sync.read(png);
}

interface DiffResult {
  canonicalId: string;
  viewport: string;
  diffPct: number;
  status: "ok" | "exceeded" | "size-mismatch" | "missing-rerun";
}

async function compareImage(baseline: string, rerun: string, diffOut: string): Promise<{ diffPct: number; status: DiffResult["status"] }> {
  if (!existsSync(rerun)) {
    return { diffPct: NaN, status: "missing-rerun" };
  }
  const [b, r] = await Promise.all([decodePng(baseline), decodePng(rerun)]);
  if (b.width !== r.width || b.height !== r.height) {
    return { diffPct: NaN, status: "size-mismatch" };
  }
  const diff = new PNG({ width: b.width, height: b.height });
  const differingPixels = pixelmatch(b.data, r.data, diff.data, b.width, b.height, {
    threshold: 0.1,
  });
  const totalPixels = b.width * b.height;
  const diffPct = (differingPixels / totalPixels) * 100;
  mkdirSync(diffOut.substring(0, diffOut.lastIndexOf("/")) || ".", { recursive: true });
  writeFileSync(diffOut, PNG.sync.write(diff));
  return { diffPct, status: "ok" };
}

function readManifestField(dir: string, field: string): string | null {
  const path = join(dir, "RUN-MANIFEST.md");
  if (!existsSync(path)) return null;
  const md = readFileSync(path, "utf-8");
  const re = new RegExp(`\\*\\*${field}:\\*\\*\\s*(\\S+)`);
  const m = md.match(re);
  return m ? m[1] : null;
}

async function main(): Promise<void> {
  const cli = parseArgs(process.argv.slice(2));

  if (!existsSync(cli.baseline)) {
    console.error(`error: baseline dir not found: ${cli.baseline}`);
    process.exit(2);
  }
  if (!existsSync(cli.rerun)) {
    console.error(`error: rerun dir not found: ${cli.rerun}`);
    process.exit(2);
  }
  mkdirSync(cli.outputDir, { recursive: true });

  // Fixture-hash equality gate (Data Engineer Phase 2 MUST-FIX): if the two
  // runs used different fixtures, this isn't a determinism failure — it's
  // fixture drift. Surface that distinction loudly.
  const bHash = readManifestField(cli.baseline, "Fixture sha256");
  const rHash = readManifestField(cli.rerun, "Fixture sha256");
  let fixtureHashOk = true;
  // The literal `<unset>` placeholder means the crawler ran without
  // V1_FIXTURE_SHA256 set. Treat it as missing (NOT as a value to compare);
  // otherwise two runs both placeholdered would produce a false-positive
  // "fixture hashes match" verdict.
  const sentinelPattern = /^<unset>$/;
  const bMissing = bHash === null || sentinelPattern.test(bHash);
  const rMissing = rHash === null || sentinelPattern.test(rHash);
  if (bMissing || rMissing) {
    console.warn(
      `warning: fixture-hash gate skipped — RUN-MANIFEST.md missing or no Fixture sha256 field (baseline=${bHash ?? "missing"}, rerun=${rHash ?? "missing"})`,
    );
  } else if (bHash !== rHash) {
    console.error(
      `error: fixture hashes diverge between baseline (${bHash}) and rerun (${rHash}). This is NOT a determinism failure — the seed dataset itself changed between runs. Re-run both crawls against the same fixture before comparing.`,
    );
    fixtureHashOk = false;
  }

  const baselineFiles = findWebPs(cli.baseline);
  const results: DiffResult[] = [];

  for (const baselineFile of baselineFiles) {
    const rel = relative(cli.baseline, baselineFile);
    const rerunFile = join(cli.rerun, rel);
    const canonicalId = rel
      .replace(/\.desktop\.webp$/, "")
      .replace(/\.mobile\.webp$/, "");
    const viewport = rel.endsWith(".desktop.webp") ? "desktop" : "mobile";
    const diffPath = join(cli.outputDir, rel.replace(/\.webp$/, ".diff.png"));

    const { diffPct, status } = await compareImage(baselineFile, rerunFile, diffPath);
    let finalStatus: DiffResult["status"] = status;
    if (status === "ok" && diffPct > cli.thresholdPct) finalStatus = "exceeded";
    results.push({ canonicalId, viewport, diffPct, status: finalStatus });
  }

  const exceeded = results.filter((r) => r.status !== "ok").length;
  const total = results.length;

  // Render report.md
  const lines = [
    "# Catalog reproducibility report",
    "",
    `**Baseline:** ${cli.baseline}`,
    `**Rerun:** ${cli.rerun}`,
    `**Threshold:** ${cli.thresholdPct}% per-image pixel diff`,
    `**Fixture hashes match:** ${fixtureHashOk ? "yes" : "NO — see error above"}`,
    "",
    "| canonical_id | viewport | diff% | status |",
    "|--------------|----------|------:|--------|",
  ];
  for (const r of results) {
    const pct = Number.isFinite(r.diffPct) ? `${r.diffPct.toFixed(4)}%` : "n/a";
    lines.push(`| ${r.canonicalId} | ${r.viewport} | ${pct} | ${r.status} |`);
  }
  lines.push("", "## Summary", "", `- Total compared: ${total}`, `- Within threshold: ${total - exceeded}`, `- Exceeded / failed: ${exceeded}`);

  const reportPath = join(cli.outputDir, "report.md");
  writeFileSync(reportPath, lines.join("\n") + "\n");

  console.log(`Total: ${total}, exceeded/failed: ${exceeded}, fixture hashes match: ${fixtureHashOk}`);
  console.log(`Report: ${reportPath}`);

  if (exceeded > 0 || !fixtureHashOk) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
