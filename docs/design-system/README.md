# Design System

shadcn/ui + Tailwind CSS token system for COREcare v2. Multi-tenant healthcare context — accessibility and clinical clarity beat visual flourish.

## Read first

[`COMPONENTS.md`](COMPONENTS.md) — how to compose shadcn/ui primitives into product components, when to extend the library, naming conventions. Start here when building anything new.

## Reference (read when the topic comes up)

| Doc | Use it for |
|---|---|
| [`TOKENS.md`](TOKENS.md) | Colors, spacing, typography, shadows, radii. **Always check tokens before hardcoding values.** |
| [`ACCESSIBILITY.md`](ACCESSIBILITY.md) | WCAG 2.1 AA targets — contrast, focus management, ARIA, keyboard navigation. Caregivers use this on phones in field conditions; a11y is non-optional. |
| [`RESPONSIVE.md`](RESPONSIVE.md) | Mobile (≤480px), tablet (481–1024px), desktop (>1024px) breakpoints. Caregiver flows are mobile-first. |
| [`BRAND.md`](BRAND.md) | Multi-tenant agency branding — logos, agency-specific colors, tenant-scoped theming. |
| [`CONTENT_GUIDE.md`](CONTENT_GUIDE.md) | User-facing copy: error messages, button labels, empty states, voice and tone. |

## Cross-references

- A11y is enforced in tests — see [`../developer/TESTING.md`](../developer/TESTING.md) for the axe-core pattern.
- Frontend code review uses the [UX Designer lens](../developer/code-review-lenses.md#ux-designer).
- The shadcn/ui choice is recorded in [ADR-008](../adr/008-shadcn-ui-component-library.md).
