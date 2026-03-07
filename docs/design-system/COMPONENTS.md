# Component Library

Built on shadcn/ui with COREcare theme overrides.

## shadcn/ui Base Components

All shadcn/ui components use HSL CSS variables from `globals.css`. Theme overrides happen at the CSS variable level, not component level.

### Installed Components

| Component | Usage in COREcare |
|-----------|------------------|
| Button | Primary actions, form submissions, navigation |
| Card | Content containers, dashboard widgets, list items |
| Dialog | Confirmations, forms, detail views |
| DropdownMenu | User menu, bulk actions, context menus |
| Form + Input + Label | All form fields with validation |
| Select | Dropdowns for role, status, agency selection |
| Table | Data tables for admin views |
| Tabs | Section navigation within pages |
| Toast | Success/error notifications |
| Tooltip | Help text, truncated content |
| Badge | Status indicators, counts, labels |
| Avatar | User photos, initials fallback |
| Calendar | Date picker for scheduling |
| Sheet | Mobile navigation drawer, side panels |
| Skeleton | Loading placeholders |
| Separator | Visual dividers |
| ScrollArea | Scrollable containers |

## Custom Domain Components

### ShiftCard

Displays a shift assignment with time, client, location, and status.

```tsx
<ShiftCard
  client="Client name"
  time="8:00 AM - 2:00 PM"
  location="123 Main St"
  status="confirmed" // confirmed | pending | in-progress | completed
  onAccept={() => {}}
  onDecline={() => {}}
/>
```

Variants: `compact` (list view), `expanded` (detail view), `calendar` (day view cell).

### VisitTimeline

Chronological list of visit events (clock-in, vitals, medications, notes, clock-out).

```tsx
<VisitTimeline
  events={[
    { type: "clock-in", time: "8:02 AM", location: { lat, lng } },
    { type: "vitals", time: "8:15 AM", data: { bp: "120/80", temp: "98.6" } },
    { type: "note", time: "9:30 AM", content: "Client in good spirits" },
  ]}
/>
```

### StatusBadge

Semantic status indicator with consistent colors across the platform.

```tsx
<StatusBadge status="active" />    // primary green
<StatusBadge status="pending" />   // lavender
<StatusBadge status="urgent" />    // coral
<StatusBadge status="completed" /> // muted
<StatusBadge status="expired" />   // destructive
```

### MetricCard

Dashboard KPI display with trend indicator.

```tsx
<MetricCard
  label="Active Caregivers"
  value={42}
  trend={{ direction: "up", percent: 12, period: "vs last month" }}
  icon={<Users />}
/>
```

### AgencySelector

Super-admin component for switching between agencies.

```tsx
<AgencySelector
  agencies={agencies}
  selected={currentAgency}
  onSelect={(agency) => {}}
  showAll // super-admin: includes "All Agencies" option
/>
```

### NotificationCenter

Bell icon dropdown with grouped notifications.

```tsx
<NotificationCenter
  unreadCount={3}
  notifications={notifications}
  onMarkRead={(id) => {}}
  onMarkAllRead={() => {}}
/>
```

## Layout Components

### DashboardLayout

Standard layout for authenticated pages: sidebar nav + header + content area.
Responsive: sidebar collapses to bottom nav on mobile.

### PlatformLayout

Super-admin layout: agency selector in header, platform-wide navigation.

### AuthLayout

Minimal layout for login/signup: centered card, branding.

## Patterns

### Loading States
- Use `<Skeleton>` for content placeholders
- Show loading spinners only for actions (button clicks, form submissions)
- Never show blank white screens

### Empty States
- Always show explanatory text and a call-to-action
- Use illustration or icon to make the empty state feel intentional

### Error States
- Inline validation: show errors below fields immediately
- API errors: toast notification with retry option
- Page-level errors: error boundary with "Try again" button

### Responsive Patterns
- Cards stack vertically on mobile, grid on desktop
- Tables become card lists on mobile
- Sidebar becomes bottom tab bar on mobile
- Dialogs become full-screen sheets on mobile
