---
name: LFS bandwidth escalation (ADR-010 Alt B)
about: File when issue #185's watch crossed Trigger C (red flag)
title: "feat(escalation): migrate v1 UI catalog off in-repo LFS — ADR-010 Alt B"
labels: documentation
---

## Context

Issue [#185](https://github.com/suniljames/COREcare-v2/issues/185)'s 30-day Git LFS bandwidth watch crossed Trigger C: monthly cumulative bandwidth exceeded 800 MB or trended above 1 GB before billing reset. Per [ADR-010](../../docs/adr/010-v1-ui-catalog-storage.md) Alternative B, the catalog migrates off in-repo LFS.

## Reading at trigger

- **Date:** _YYYY-MM-DD_
- **Bandwidth used:** _XXX_ MB / 1024 MB
- **Reset day:** _YYYY-MM-DD_

## Decision required: pick one

- [ ] **(a)** Move the catalog to a `gh-pages` branch in this repo with LFS removed from the new branch
- [ ] **(b)** Move the catalog to a new repo `coreacare-v1-catalog/` with its own LFS quota
- [ ] **(c)** Build the catalog as a static-site artifact (Vercel / Netlify) and remove from this repo

The follow-up implementer evaluates the picked option's tradeoffs. ADR-010 lists the original analysis. This template does not pre-decide.

## Linked artifacts

- Watch issue: #185
- ADR-010: `docs/adr/010-v1-ui-catalog-storage.md`
- Runbook: `docs/operations/lfs-bandwidth-watch.md`
