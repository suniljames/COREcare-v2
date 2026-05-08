# Mockups

Visual reference images for COREcare v2 features. **Not a spec.** The running application is the source of truth; mockups may lag implementation.

## Convention

Mockups are organized by issue or feature directory (e.g., `125/` for issue #125). Each subdirectory contains the visual targets for a specific piece of work.

## When to use mockups

- **Building a feature:** check whether a mockup directory exists for your issue. If yes, use it as a starting visual target.
- **Reviewing a PR:** if a mockup exists for the issue, check whether the implementation reflects the intent (not pixel-perfection).
- **Designing something new:** prefer creating a mockup *before* implementation when the visual is non-obvious.

## When *not* to use mockups

- **As a spec for behavior** — mockups capture visual intent, not interaction logic, edge cases, or accessibility requirements. Those live in the issue body, [`../design-system/`](../design-system/), and [`../developer/code-review-lenses.md`](../developer/code-review-lenses.md).
- **As an authoritative reference** — if a mockup and the running app disagree, the running app wins (or both are wrong, but the mockup is staler).

## Cross-references

- Design system rules and component library: [`../design-system/README.md`](../design-system/README.md).
- Accessibility standards (mockups don't always show focus / contrast / a11y states): [`../design-system/ACCESSIBILITY.md`](../design-system/ACCESSIBILITY.md).
