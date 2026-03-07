# PRD Template

Use this template when composing a Product Requirements Document. Every section
is **required** — use "N/A" with a brief rationale if a section does not apply.

---

```markdown
## Product Requirements Document

**Issue:** #<number>
**PM Review Date:** <YYYY-MM-DD>
**Status:** Draft

---

### 1. Problem Statement

<What user problem does this solve? Who feels the pain? How severe is it?
Frame from the end-user's perspective, not the engineering team's.>

### 2. User Personas Affected

<Which user types are impacted? For each persona, describe their relationship
to this problem:>

| Persona | Impact | Context |
|---------|--------|---------|
| e.g., Family Member | Primary | ... |
| e.g., Caregiver (Nurse) | Secondary | ... |
| e.g., Agency Admin | Operational | ... |
| e.g., Super-Admin | Platform | ... |

### 3. User Stories / Jobs to Be Done

1. ...
2. ...
3. ...

### 4. Success Criteria

<Measurable, observable outcomes. Write as testable statements.>

- [ ] ...
- [ ] ...
- [ ] ...

### 5. Scope

**In scope:**
- ...

**Out of scope (and why):**
- ...

### 6. User Experience Requirements

<Expected user flow. What does the user see, tap, read? What feedback?
What error states? Keep it behavioral, not technical.>

### 7. Privacy & Compliance Considerations

<ALWAYS include. Does this feature create, display, transmit, or store PHI?
Who can see what? Consent or access control implications? HIPAA logging?>

### 8. Multi-Tenancy Considerations

<How does this feature behave across tenants? Super-admin view vs agency view?
Data isolation requirements? Cross-tenant visibility rules?>

### 9. Documentation & Audit Requirements

<What should be logged? What user-facing help text or documentation is needed?>

### 10. Related Issues

| Issue | Relationship | Summary |
|-------|-------------|---------|
| #... | Prerequisite / Related / Follow-up | ... |

### 11. Open Questions

1. ...

### 12. Recommendation

<Overall product recommendation. Build as described? With modifications? Priority?>
```
