#!/usr/bin/env bash
# Prints the operator procedure for reading Git LFS bandwidth from
# GitHub Settings -> Billing, plus a copy-paste comment template for
# the 30-day post-#107 bandwidth report on issue #185.
#
# This script does NOT make any network calls. The bandwidth meter for
# personal-account repos is web-only; the operator transcribes the
# reading into the comment template manually. See ADR-010, issue #185
# System Architect review, and docs/operations/lfs-bandwidth-watch.md
# for the full rationale.
#
# Usage:
#   scripts/lfs-bandwidth-snapshot.sh
#   scripts/lfs-bandwidth-snapshot.sh | gh issue comment 185 --repo suniljames/COREcare-v2 --body-file -

set -u

today=$(date +%F)

cat <<EOF
============================================================
 Git LFS bandwidth snapshot — operator procedure
 Today: $today
============================================================

STEP 1 — Open the GitHub billing panel for your account:
  https://github.com/settings/billing

STEP 2 — Locate the "Git LFS Data" section. Record:
  - bandwidth used this period (MB)
  - bandwidth quota (MB; expect 1024 MB / 1 GB on free tier)
  - reset date for the current billing period

STEP 3 — Take a screenshot of the panel. Attach to the report comment.

STEP 4 — Copy the template below, fill the TBDs, post via:
  gh issue comment 185 --repo suniljames/COREcare-v2 --body-file <path>

See docs/operations/lfs-bandwidth-watch.md for the full runbook,
including yellow-flag and red-flag templates and the reset-day caveat.

============================================================
 Day-30 report comment template
============================================================
**30-day Git LFS bandwidth report** for [\`docs/legacy/v1-ui-catalog/\`](https://github.com/suniljames/COREcare-v2/tree/main/docs/legacy/v1-ui-catalog) (post-#107 merge).

**Period:** 2026-05-07 → 2026-06-07
**Reading taken on:** $today
**Bandwidth used (account-wide):** _TBD_ MB / 1024 MB free-tier quota
**Largest single CI run observed:** _TBD_ MB (workflow: _TBD_)
**Reset day(s) within window:** _TBD_

_Screenshot of Settings → Billing → Git LFS Data attached below._

**Outcome:** [Threshold not approached → closing as resolved.] *or* [Yellow flag triggered on _date_; mitigation _link_.] *or* [Red flag → ADR-010 follow-up filed at _link_.]
EOF
