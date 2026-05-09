# ADR-008: shadcn/ui Component Library

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-001 (Architecture)

## Context

COREcare v2 needs a component library that provides accessible, customizable UI components. The design system emphasizes warm, calming aesthetics with soothing color pops — not a generic corporate look.

Options:
1. **Material UI (MUI)** — comprehensive, opinionated design language (Google Material)
2. **Chakra UI** — good DX, but styling approach conflicts with Tailwind
3. **shadcn/ui** — copy-paste components built on Radix UI + Tailwind CSS
4. **Headless UI** — unstyled, maximum flexibility, more work
5. **Custom from scratch** — maximum control, maximum effort

## Decision

Use **shadcn/ui** as the component foundation.

### Why shadcn/ui
- **Copy-paste, not dependency** — components will live in our codebase under `web/src/components/ui/` (directory created on first component), fully customizable
- **Radix UI primitives** — accessible by default (ARIA, keyboard nav, focus management)
- **Tailwind CSS native** — integrates perfectly with our design token system
- **HSL CSS variables** — theming via CSS custom properties, matching our `TOKENS.md`
- **Not a black box** — we own the code, can modify anything without forking

### Theme Integration
- All shadcn components use CSS variables defined in `globals.css`
- COREcare's design tokens (greens, lavender, coral, sky) are mapped to shadcn's semantic tokens
- Custom domain components (ShiftCard, VisitTimeline, StatusBadge) extend shadcn primitives

## Consequences

### Positive
- Full control over every component's markup and styling
- Accessible out of the box (Radix UI handles ARIA, focus, keyboard)
- Tailwind integration is seamless — no CSS-in-JS conflicts
- Easy to maintain — components are just files in our repo
- Great documentation and community

### Negative
- Must manually add each component (not installed as a package)
- No automatic updates — must manually merge upstream changes
- Some components need significant customization for our design system
- Smaller ecosystem than MUI (fewer pre-built complex components)

### Risks
- Component drift from upstream — mitigate by documenting customizations
- Accessibility regression when customizing — mitigate by keeping Radix primitives intact
