# Accessibility

## Standard

WCAG 2.1 Level AA compliance. Target AAA where feasible (especially touch targets and contrast).

## Color Contrast

| Element | Minimum Ratio | Standard |
|---------|--------------|----------|
| Body text on background | 4.5:1 | AA |
| Large text (>=18px bold, >=24px) | 3:1 | AA |
| UI components (borders, icons) | 3:1 | AA |
| Focus indicators | 3:1 | AA |

All color tokens in `TOKENS.md` are verified against these ratios. Use the `--foreground` / `--muted-foreground` tokens — never hardcode gray values.

## Focus Management

### Keyboard Navigation
- All interactive elements reachable via Tab
- Logical tab order (matches visual reading order)
- Skip-to-content link as first focusable element
- Focus trapped inside modals/dialogs when open
- Focus restored to trigger element when modal closes

### Focus Indicators
- 2px solid ring using `--ring` token (primary green)
- Offset: 2px from element edge
- Never remove outline without providing an alternative
- `:focus-visible` only (not `:focus`) to avoid showing on mouse clicks

```css
/* Applied by shadcn/ui's focus-visible utility */
focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
```

## ARIA Patterns

### Live Regions
- Toast notifications: `role="status"` with `aria-live="polite"`
- Error messages: `role="alert"` with `aria-live="assertive"`
- Loading states: `aria-busy="true"` on container

### Landmarks
- `<header>` / `role="banner"` — page header
- `<nav>` / `role="navigation"` — primary + secondary nav (use `aria-label` to distinguish)
- `<main>` / `role="main"` — primary content
- `<aside>` / `role="complementary"` — sidebar, filters
- `<footer>` / `role="contentinfo"` — page footer

### Forms
- Every input has an associated `<label>` (visible or `sr-only`)
- Error messages linked via `aria-describedby`
- Required fields marked with `aria-required="true"`
- Form groups wrapped in `<fieldset>` with `<legend>`

### Data Tables
- Use `<th scope="col">` for column headers
- Use `<th scope="row">` for row headers
- Complex tables: `aria-describedby` linking to caption
- Sortable columns: `aria-sort="ascending|descending|none"`

### Custom Components
- Tabs: `role="tablist"`, `role="tab"`, `role="tabpanel"` with `aria-selected`
- Dialogs: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Dropdowns: `role="menu"`, `role="menuitem"`, arrow key navigation
- Status badges: Include `sr-only` text if color is the only differentiator

## Motion

- Respect `prefers-reduced-motion`: disable animations, transitions, and auto-play
- All animations CSS-only (no JS-driven motion)
- Duration: 150-300ms for micro-interactions, 300-500ms for page transitions
- Easing: `ease-out` for entrances, `ease-in` for exits

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Screen Reader Testing

Test with:
- **VoiceOver** (macOS/iOS) — primary
- **NVDA** (Windows) — secondary
- **axe DevTools** browser extension — automated checks

### Key flows to verify:
1. Login and authentication
2. Dashboard navigation
3. Shift acceptance/decline
4. Form submission (charting, visit notes)
5. Notification interaction
6. Table navigation (admin views)
