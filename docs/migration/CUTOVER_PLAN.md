# COREcare v1 → v2 Cutover Plan

## Overview

This document describes the process for migrating from COREcare v1 (Django) to v2 (FastAPI + Next.js). The migration is designed as a zero-downtime parallel run with a clean cutover point.

## Pre-Cutover Checklist

- [ ] All v2 features have passing tests (119+ tests)
- [ ] Docker Compose stack starts cleanly (`docker compose up --build`)
- [ ] Health endpoint returns 200 (`curl http://localhost:8000/healthz`)
- [ ] v1 database export script validated against test data
- [ ] Migration service dry-run completed without errors
- [ ] All user accounts have been mapped (v1 → v2 roles)
- [ ] Clerk authentication configured and tested
- [ ] DNS/reverse proxy configuration ready

## Migration Steps

### Phase 1: Data Export (v1)

```bash
# Export v1 data to JSON
python manage.py export_data --output v1_export.json
```

Expected export format:
```json
{
  "agencies": [...],
  "users": [...],
  "clients": [...],
  "shifts": [...],
  "visits": [...],
  "credentials": [...]
}
```

### Phase 2: Data Import (v2)

```python
from app.services.migration import MigrationService

migrator = MigrationService(session)
report = await migrator.run_full_migration(v1_data)
print(report.to_dict())
```

### Phase 3: Parallel Run

- v1 continues serving production traffic
- v2 runs in shadow mode on separate port
- Compare outputs for key operations (shift list, client list)
- Duration: 1-2 weeks

### Phase 4: Cutover

1. Set v1 to read-only mode
2. Run final delta migration (any data created during parallel run)
3. Switch DNS/proxy to point to v2
4. Verify all endpoints responding
5. Monitor for 24 hours

### Phase 5: Post-Cutover

- Keep v1 running in read-only for 30 days (rollback safety net)
- Monitor v2 error rates and performance
- Decommission v1 after 30-day window

## Rollback Plan

If critical issues are found during cutover:

1. Switch DNS/proxy back to v1
2. Any data created in v2 during the cutover window will need manual reconciliation
3. Root cause analysis before re-attempting

## Data Mapping

| v1 Entity | v2 Entity | Notes |
|-----------|-----------|-------|
| Agency | Agency | Direct mapping |
| User (admin) | User (AGENCY_ADMIN) | Role promotion |
| User (manager) | User (CARE_MANAGER) | New role tier |
| User (caregiver) | User (CAREGIVER) | Direct |
| User (family) | User (FAMILY) | Direct |
| Client | Client | Added status field |
| Shift | Shift | Added recurrence_rule |
| Visit | Visit | Added GPS fields |
| — | ChartTemplate | New in v2 |
| — | Chart | New in v2 |
| — | Credential | New in v2 |
| — | PayrollPeriod | New in v2 |
| — | Invoice | New in v2 |
| — | Notification | New in v2 |
| — | AIConversation | New in v2 |
