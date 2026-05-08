---
canonical_id: agency-admin/012-stats
route: /admin/view-as/stats/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — JSON endpoint returning View As session counters and rate-limit headroom; the captured WebP is the browser's raw-JSON view (see Interaction notes for the field schema).

**Interaction notes:**
- Endpoint → `view_as_stats` returns `{user_stats: {sessions_last_hour, sessions_last_day, sessions_last_week, total_sessions}, rate_limit: {max_per_hour, current_hour_count}}` plus the staff caller's current rate-limit headroom (`max_per_hour: 10, current_hour_count: 0` in the captured response — clean fixture).
- Used by → admin tooling to surface "approaching rate limit" hints before a start is rejected; counters drive operational dashboards.
- Rate-limit policy → caps initiated sessions per staff caller per hour; exceeded attempts produce an audit row visible at [agency-admin/013-audit-log](013-audit-log.md) without starting a session.
- Aggregation window → counters are computed on the fly from the audit log; no denormalization, so callers should treat them as point-in-time.
- Untrusted output → consumers must HTML-escape any rendered counter labels.
