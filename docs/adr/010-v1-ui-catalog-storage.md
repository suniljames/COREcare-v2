# ADR-010: v1 UI Screenshot Catalog Storage

**Status:** Accepted
**Date:** 2026-05-07
**Related:** [#79](https://github.com/suniljames/COREcare-v2/issues/79) (engineering committee design synthesis)

## Context

Issue [#79](https://github.com/suniljames/COREcare-v2/issues/79) commits a per-persona screenshot catalog of v1 (`COREcare-access`) to v2 under `docs/legacy/v1-ui-catalog/` so collaborators without v1 source access can see UX ground truth.

Estimated output: 6 personas × ~50–80 distinct routes × 2 viewports (desktop + mobile) ≈ 500–800 image files. At unoptimized PNG sizes typical of text-heavy admin UIs (~500 KB each), this is **~250–400 MB of binary blobs** committed permanently to the v2 git history.

Three constraints make this material:
- v2's local Docker Compose / Mac Mini deployment story (see [`docs/developer/project-context.md`](../developer/project-context.md)) prefers operational simplicity. Bloating every clone, every CI run, and every worktree with hundreds of MB undermines that.
- The catalog is one-shot: regenerated only on explicit refresh (per #79 Out of Scope). Most contributors will never need to look at the binaries; they read the captions.
- Test fixtures, ADRs, and migration prose stay in regular git for diff/blame; only the binary artifacts need different handling.

## Decision

**Adopt Git LFS + WebP q=80 for the v1 UI catalog binaries.**

1. **Compress to WebP at q=80** before committing. WebP at q=80 typically halves PNG byte-size on text-heavy screenshots without visible quality loss. Cuts the on-disk and in-LFS cost by ~50%.
2. **Track `docs/legacy/v1-ui-catalog/**/*.webp` via Git LFS.** Image files become git pointers in the working tree; the actual blobs live in LFS storage and are pulled on demand.
3. **Captions, READMEs, and the run manifest remain in regular git.** They are markdown, diff-friendly, and the primary contributor-readable surface.
4. **CI pulls LFS conditionally.** Workflows that touch the catalog (`check-v1-catalog-coverage`, future catalog-validation runs) do `lfs pull`; workflows that do not touch it skip LFS smudging via `git lfs install --skip-smudge` or per-job `LFS_SKIP_SMUDGE=1`.

## Alternatives considered

### A. Commit raw PNGs in regular git (no LFS, no WebP)

Simplest. Rejected: 250–400 MB committed in regular git is a permanent tax on every clone, every fork, every CI run, every worktree creation. Once committed, history rewrite is the only way out.

### B. Publish the catalog to a separate static site or `gh-pages` branch

Lowest impact on v2's git size. Rejected for v1.0:
- Loses "browse in your IDE" affordance — collaborators using Claude Code or local editors lose direct file access.
- Requires extra publishing infra (CI workflow + token + URL pinning).
- Catalog → migration-doc cross-references break across repository boundaries.

We may revisit this if LFS bandwidth quota becomes a real constraint.

### C. WebP without LFS

Cuts size but binary blobs still live in regular git. Saves ~50% but the fundamental problem (pack file growth, slow clones) remains. LFS is the right control regardless of compression.

## Consequences

### Positive

- v2 clones stay lean for the ~95% of contributors who never need the catalog binaries (LFS smudging skipped by default).
- Coverage check, captions, and READMEs work natively because they remain in regular git.
- Reproducibility is preserved: the LFS pointers are versioned alongside the captions, so a catalog refresh produces a clean git diff.

### Negative

- Adds a dependency to v2's developer setup: `git lfs install` becomes a step in [`CONTRIBUTING.md`](../../CONTRIBUTING.md). Without it, contributors clone pointer files and do not notice until they open a `.webp`.
- GitHub LFS has quota caps (storage + bandwidth). Frequent re-runs or wide CI fan-out could exhaust the bandwidth allowance; #79 PR-C is the first real test.
- Worktree behavior with LFS: the v2 dotfiles automation creates worktrees frequently. LFS pointers are correctly inherited by worktrees, but the LFS object cache lives at the repo root — verified compatible during PR-A development.
- One-way decision: removing LFS later requires `git lfs migrate` history rewrite, which is disruptive. Commit to this only after the ADR review.

### Neutral

- WebP q=80 is widely supported in modern browsers; viewing in a Markdown preview pane works in VS Code, GitHub.com, and JetBrains IDEs out of the box.

## Implementation hooks

This ADR gates [#79](https://github.com/suniljames/COREcare-v2/issues/79) PR-A's `.gitattributes` rule + [`CONTRIBUTING.md`](../../CONTRIBUTING.md) update + future PR-C catalog commit. The implementation lives in the same scaffolding PR as this ADR; a follow-up PR-C runs the crawler and lands the actual binaries via LFS.

If LFS bandwidth proves problematic in practice, revisit Alternative B (separate static site).
