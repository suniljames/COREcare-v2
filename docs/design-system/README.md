# Design System

shadcn/ui + Tailwind CSS token system for COREcare v2. Multi-tenant healthcare context — accessibility and clinical clarity beat visual flourish.

## Read first

[`COMPONENTS.md`](COMPONENTS.md) — the target shadcn/ui component surface for COREcare v2 (forward-looking spec; most components are not yet implemented). Use it as the contract when building anything new.

## Reference (read when the topic comes up)

| Doc | Use it for |
|---|---|
| [`TOKENS.md`](TOKENS.md) | Colors, spacing, typography, shadows, radii. **Always check tokens before hardcoding values.** |
| [`ACCESSIBILITY.md`](ACCESSIBILITY.md) | WCAG 2.1 AA targets — contrast, focus management, ARIA, keyboard navigation. Caregivers use this on phones in field conditions; a11y is non-optional. |
| [`RESPONSIVE.md`](RESPONSIVE.md) | Mobile (<640px), tablet (≥640px), desktop (≥1024px), wide (≥1280px) — Tailwind's default breakpoints. Caregiver flows are mobile-first. |
| [`BRAND.md`](BRAND.md) | Multi-tenant agency branding — logos, agency-specific colors, tenant-scoped theming. |
| [`CONTENT_GUIDE.md`](CONTENT_GUIDE.md) | User-facing copy: error messages, button labels, empty states, voice and tone. |

## Cross-references

- Frontend code review uses the [UX Designer lens](../developer/code-review-lenses.md#ux-designer).
- The shadcn/ui choice is recorded in [ADR-008](../adr/008-shadcn-ui-component-library.md).
