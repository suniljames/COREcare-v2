# Design Tokens

All tokens are defined as CSS custom properties (HSL format) and mapped to `tailwind.config.ts`.

## Color Palette

### Primary — Soothing Greens

| Token | HSL | Tailwind | Usage |
|-------|-----|----------|-------|
| `--primary-50` | 145 60% 96% | `primary-50` | Subtle backgrounds |
| `--primary-100` | 146 55% 90% | `primary-100` | Hover backgrounds |
| `--primary-200` | 147 50% 80% | `primary-200` | Borders, dividers |
| `--primary-300` | 148 45% 65% | `primary-300` | Secondary icons |
| `--primary-400` | 150 42% 50% | `primary-400` | Active states |
| `--primary-500` | 152 45% 40% | `primary-500` | Primary buttons, links |
| `--primary-600` | 153 48% 33% | `primary-600` | Hover on primary |
| `--primary-700` | 155 50% 26% | `primary-700` | Headings, emphasis |
| `--primary-800` | 156 52% 20% | `primary-800` | Dark accents |
| `--primary-900` | 158 55% 14% | `primary-900` | Darkest shade |

### Lavender Accent

| Token | HSL | Usage |
|-------|-----|-------|
| `--lavender-50` | 260 60% 97% | Background tint |
| `--lavender-100` | 261 55% 92% | Selected row |
| `--lavender-200` | 262 50% 82% | Badge background |
| `--lavender-300` | 263 45% 70% | Icon fill |
| `--lavender-400` | 264 40% 60% | Border accent |
| `--lavender-500` | 265 42% 52% | AI feature indicator |

### Coral Accent

| Token | HSL | Usage |
|-------|-----|-------|
| `--coral-50` | 12 80% 97% | Alert background |
| `--coral-100` | 13 75% 92% | Warning highlight |
| `--coral-200` | 14 70% 82% | Notification dot |
| `--coral-300` | 15 65% 70% | Urgency indicator |
| `--coral-400` | 16 60% 60% | Error text |
| `--coral-500` | 17 62% 52% | Critical action |

### Sky Accent

| Token | HSL | Usage |
|-------|-----|-------|
| `--sky-50` | 200 70% 97% | Info background |
| `--sky-100` | 201 65% 92% | Link hover |
| `--sky-200` | 202 60% 82% | Progress bar |
| `--sky-300` | 203 55% 70% | Chart secondary |
| `--sky-400` | 204 50% 60% | Interactive element |
| `--sky-500` | 205 52% 52% | Link color |

### Semantic (shadcn/ui)

| Token | HSL | Usage |
|-------|-----|-------|
| `--background` | 0 0% 100% | Page background |
| `--foreground` | 220 20% 14% | Primary text |
| `--muted` | 220 14% 96% | Muted backgrounds |
| `--muted-foreground` | 220 10% 46% | Secondary text |
| `--border` | 220 13% 91% | Borders |
| `--destructive` | 0 72% 51% | Delete, error actions |
| `--ring` | 152 45% 40% | Focus ring (matches primary) |

## Typography

| Element | Font | Weight | Size | Line Height |
|---------|------|--------|------|-------------|
| Display heading | Inter (--font-inter) | 700 | 2.25rem (36px) | 1.2 |
| H1 | Inter | 700 | 1.875rem (30px) | 1.2 |
| H2 | Inter | 600 | 1.5rem (24px) | 1.3 |
| H3 | Inter | 600 | 1.25rem (20px) | 1.4 |
| Body | Inter | 400 | 1rem (16px) | 1.5 |
| Small | Inter | 400 | 0.875rem (14px) | 1.4 |
| Caption | Inter | 500 | 0.75rem (12px) | 1.3 |

Font stack: `Inter, system-ui, -apple-system, sans-serif`

## Spacing (8px Grid)

| Token | Value | Tailwind |
|-------|-------|----------|
| xs | 4px | `1` |
| sm | 8px | `2` |
| md | 16px | `4` |
| lg | 24px | `6` |
| xl | 32px | `8` |
| 2xl | 48px | `12` |
| 3xl | 64px | `16` |

## Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | 0 1px 2px rgba(0,0,0,0.05) | Cards, inputs |
| `--shadow-md` | 0 4px 6px rgba(0,0,0,0.07) | Dropdowns, popovers |
| `--shadow-lg` | 0 10px 15px rgba(0,0,0,0.1) | Modals, dialogs |

## Border Radius

| Token | Value | Tailwind |
|-------|-------|----------|
| `--radius` | 0.625rem (10px) | `rounded-lg` |
| md | calc(var(--radius) - 2px) = 8px | `rounded-md` |
| sm | calc(var(--radius) - 4px) = 6px | `rounded-sm` |
| full | 9999px | `rounded-full` |
