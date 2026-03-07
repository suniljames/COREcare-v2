# Responsive Design

## Mobile-First Philosophy

COREcare users primarily interact via smartphone — caregivers during shifts, families checking updates, managers on the go. Every design starts mobile and scales up.

## Breakpoints

| Name | Width | Tailwind | Target |
|------|-------|----------|--------|
| Mobile | < 640px | default | Smartphones (primary) |
| Tablet | >= 640px | `sm:` | iPad, large phones landscape |
| Desktop | >= 1024px | `lg:` | Laptop, desktop |
| Wide | >= 1280px | `xl:` | Large monitors, super-admin |

## Touch Targets

- **Minimum:** 44x44px (WCAG 2.5.5 AAA, Apple HIG)
- **Recommended:** 48x48px for primary actions
- **Spacing:** 8px minimum between adjacent targets
- **Bottom nav items:** Full width of column, 56px height

## Layout Patterns

### Navigation
- **Mobile:** Bottom tab bar (5 items max) + hamburger for overflow
- **Tablet:** Collapsible sidebar (icon-only when collapsed)
- **Desktop:** Full sidebar with labels

### Data Display
- **Mobile:** Stacked cards, one per row
- **Tablet:** 2-column card grid
- **Desktop:** Data tables with sortable columns

### Forms
- **Mobile:** Full-width inputs, stacked labels above fields
- **Tablet+:** Side-by-side fields where semantically grouped (e.g., first/last name)

### Dialogs
- **Mobile:** Full-screen sheets (slide up from bottom)
- **Tablet+:** Centered dialog with overlay

### Calendar/Schedule
- **Mobile:** Day view (default), swipe for days
- **Tablet:** 3-day view
- **Desktop:** Full week view

## PWA Safe Areas

```css
/* Account for notch, home indicator, status bar */
padding-top: env(safe-area-inset-top);
padding-bottom: env(safe-area-inset-bottom);
padding-left: env(safe-area-inset-left);
padding-right: env(safe-area-inset-right);
```

Apply safe areas to:
- Bottom navigation bar
- Fixed headers
- Full-screen sheets/modals
- Floating action buttons

## Performance

- Images: `<Image>` component with `sizes` prop for responsive loading
- Fonts: `next/font` with `display: swap`
- Critical CSS: Tailwind purges unused styles automatically
- Lazy load: Below-fold content, heavy components (charts, calendars)
