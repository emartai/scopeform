# Scopeform — design system

This file is the single source of truth for every visual and UX decision in Scopeform. Claude Code and any frontend work must follow these rules exactly.

---

## Brand identity

### Logo concept
The Scopeform logo is a **token ring with a green center dot**. The metaphor is deliberate: a live agent inside a controlled boundary. The ring represents the scope/boundary. The dot represents the active agent inside it.

### Logo construction
- **Ring**: thin circle, white at ~45% opacity. It recedes into the background so the dot leads visually. In dark sidebar context it reads as a faint orbit. In light/docs context it avoids feeling corporate.
- **Dot**: solid `#22c55e` (green). This is the only saturated color element in the mark.
- **Wordmark**: lowercase `scopeform`, clean sans-serif (Inter), font-weight 600. Always lowercase — never "Scopeform" in the wordmark.

### Logo usage rules
| Context | What to show |
|---|---|
| Sidebar (collapsed or expanded) | Icon + wordmark side by side |
| Favicon | Icon only (40px, 24px, 16px sizes) |
| Landing page navbar | Icon + wordmark |
| Auth screen | Icon + wordmark, centered |
| Inside tables or logs | No logo — never repeat in data rows |
| Docs / light background | Icon + wordmark, same construction |

### Logo SVG (implement this exactly)
```svg
<!-- Icon: token ring with green dot -->
<svg viewBox="0 0 32 32" fill="none">
  <!-- Ring: white, ~45% opacity -->
  <circle cx="16" cy="16" r="12" stroke="white" stroke-width="1.5" stroke-opacity="0.45" fill="none"/>
  <!-- Inner ring detail (subtle) -->
  <circle cx="16" cy="16" r="8" stroke="white" stroke-width="0.75" stroke-opacity="0.2" fill="none"/>
  <!-- Green dot: the agent -->
  <circle cx="16" cy="16" r="4" fill="#22c55e"/>
</svg>
```

### Size variants
- **Large** (sidebar, landing): 40px icon + wordmark at 22px/600
- **Medium** (top bar, auth): 24px icon + wordmark at 16px/600
- **Small/favicon**: 16px icon only

---

## Color system

### Base palette (dark mode — primary)
| Token | Hex | Usage |
|---|---|---|
| `bg-base` | `#0a0a0a` | Page background |
| `bg-card` | `#111111` | Card, sidebar background |
| `bg-elevated` | `#161616` | Hover states, table row hover |
| `bg-subtle` | `#1a1a1a` | Input backgrounds, code blocks |
| `border-default` | `#1f1f1f` | All borders, dividers |
| `border-muted` | `#2a2a2a` | Subtle borders inside cards |
| `text-primary` | `#ffffff` | Headings, important labels |
| `text-secondary` | `#a1a1aa` | Body text, descriptions |
| `text-tertiary` | `#52525b` | Placeholders, very muted labels |

### Semantic colors
| Meaning | Color | Hex | Usage |
|---|---|---|---|
| Active / allowed / success | Green | `#22c55e` | Active badge, allowed log row, brand dot |
| Revoked / blocked / danger | Red | `#ef4444` | Revoked badge, blocked log row, revoke button |
| Expiring / warning | Yellow | `#eab308` | Expiring token badge |
| Inactive / decommissioned | Gray | `#52525b` | Inactive badge, disabled states |
| Info / production | Blue | `#3b82f6` | Production environment badge |
| Staging | Purple | `#a855f7` | Staging environment badge |
| Development | Gray/teal | `#14b8a6` | Development environment badge |

### Badge color map
```
Status badges:
  active        → bg: #052e16  text: #22c55e  border: #166534
  suspended     → bg: #451a03  text: #eab308  border: #854d0e
  decommissioned → bg: #18181b text: #52525b  border: #27272a
  revoked       → bg: #450a0a  text: #ef4444  border: #7f1d1d

Environment badges:
  production    → bg: #0c1a3a  text: #3b82f6  border: #1e3a5f
  staging       → bg: #2d1b4e  text: #a855f7  border: #4a1d78
  development   → bg: #042f2e  text: #14b8a6  border: #0d4039

Log status:
  allowed       → no tint (normal row)
  blocked       → row bg: #1a0505  subtle red left border: 2px solid #ef4444
```

---

## Typography

### Font stack
```css
/* UI font — all interface text */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Monospace — agent names, tokens, logs, CLI */
font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
```

### Load via Google Fonts (in layout.tsx)
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Type scale
| Role | Size | Weight | Font | Color |
|---|---|---|---|---|
| Page title | 20px | 600 | Inter | `#ffffff` |
| Section heading | 14px | 600 | Inter | `#ffffff` |
| Body / table cell | 13px | 400 | Inter | `#a1a1aa` |
| Label / muted | 12px | 400 | Inter | `#52525b` |
| Agent name | 13px | 500 | JetBrains Mono | `#ffffff` |
| Token value | 12px | 400 | JetBrains Mono | `#a1a1aa` |
| Log entry | 12px | 400 | JetBrains Mono | `#a1a1aa` |
| CLI snippet | 13px | 400 | JetBrains Mono | `#22c55e` |
| Timestamp | 12px | 400 | JetBrains Mono | `#52525b` |

### Monospace elements (always use JetBrains Mono)
- Agent names in all tables and detail pages
- Token values (masked as `sf_••••••••abcd`)
- Log service/action fields (`openai/chat.completions`)
- Timestamps in logs
- CLI code blocks
- Agent IDs

---

## Layout

### Global shell
```
┌─────────────────────────────────────────────────────┐
│ Sidebar (240px fixed)  │  Main content area          │
│                        │  ┌────────────────────────┐ │
│  Logo                  │  │ Top bar (48px)          │ │
│  ─────                 │  ├────────────────────────┤ │
│  Nav links             │  │                        │ │
│                        │  │ Page content           │ │
│                        │  │ (max-width: 1200px)    │ │
│                        │  │                        │ │
└─────────────────────────────────────────────────────┘
```

### Sidebar
- Width: 240px, fixed
- Background: `#111111`
- Right border: `1px solid #1f1f1f`
- Padding: 16px 12px
- Logo section: 40px height, 16px bottom margin, 16px bottom border `#1f1f1f`
- Nav item height: 32px
- Nav item padding: 0 8px
- Nav item border-radius: 6px
- Active nav item: bg `#1a1a1a`, text `#ffffff`
- Inactive nav item: text `#a1a1aa`, hover bg `#161616`
- Nav icon: 15px, same color as text
- Active indicator: 2px left bar `#22c55e` (only on active item)

### Top bar
- Height: 48px
- Background: `#0a0a0a`
- Bottom border: `1px solid #1f1f1f`
- Padding: 0 24px
- Left: breadcrumb or page title (13px, `#a1a1aa`)
- Right: org name (13px, `#ffffff`) + avatar circle (28px)

### Main content
- Padding: 24px
- Max-width: 1200px
- Page header: title (20px/600) + action button, margin-bottom 20px

---

## Components

### Cards
```css
background: #111111;
border: 1px solid #1f1f1f;
border-radius: 8px;
padding: 16px 20px;
```

### Tables
```css
/* Table wrapper */
border: 1px solid #1f1f1f;
border-radius: 8px;
overflow: hidden;

/* Header row */
background: #111111;
border-bottom: 1px solid #1f1f1f;
height: 36px;
font-size: 11px;
font-weight: 500;
color: #52525b;
text-transform: uppercase;
letter-spacing: 0.04em;
padding: 0 16px;

/* Data rows */
height: 48px;
padding: 0 16px;
border-bottom: 1px solid #1f1f1f;
font-size: 13px;
color: #a1a1aa;

/* Last row: no border-bottom */

/* Row hover */
background: #161616;
cursor: pointer;

/* Blocked log row */
background: #1a0505;
border-left: 2px solid #ef4444;
```

### Buttons
```css
/* Primary */
background: #ffffff;
color: #0a0a0a;
font-size: 13px;
font-weight: 500;
height: 32px;
padding: 0 12px;
border-radius: 6px;
border: none;

/* Secondary / outline */
background: transparent;
color: #a1a1aa;
border: 1px solid #1f1f1f;
height: 32px;
padding: 0 12px;
border-radius: 6px;

/* Danger (Revoke) */
background: transparent;
color: #ef4444;
border: 1px solid #7f1d1d;
height: 28px;
padding: 0 10px;
border-radius: 5px;
font-size: 12px;

/* Danger hover */
background: #450a0a;
border-color: #ef4444;
```

### Badges
```css
/* Base badge */
display: inline-flex;
align-items: center;
height: 20px;
padding: 0 8px;
border-radius: 4px;
font-size: 11px;
font-weight: 500;
border: 1px solid;
/* Colors from badge color map above */

/* Dot indicator (optional, for status badges) */
width: 5px;
height: 5px;
border-radius: 50%;
margin-right: 5px;
```

### Code blocks / CLI snippets
```css
background: #111111;
border: 1px solid #1f1f1f;
border-radius: 6px;
padding: 12px 16px;
font-family: 'JetBrains Mono', monospace;
font-size: 13px;
color: #22c55e;  /* green for CLI commands */

/* Prompt character */
color: #52525b;  /* gray $ prefix */
```

### Inputs
```css
background: #111111;
border: 1px solid #1f1f1f;
border-radius: 6px;
height: 32px;
padding: 0 10px;
font-size: 13px;
color: #ffffff;
outline: none;

/* Focus */
border-color: #3f3f46;
box-shadow: 0 0 0 1px #3f3f46;

/* Placeholder */
color: #52525b;
```

### Skeleton loaders
```css
background: linear-gradient(90deg, #161616 25%, #1f1f1f 50%, #161616 75%);
background-size: 200% 100%;
animation: shimmer 1.5s infinite;
border-radius: 4px;

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Toast notifications
- Position: bottom-right, 16px from edge
- Background: `#111111`
- Border: `1px solid #1f1f1f`
- Border-radius: 8px
- Padding: 12px 16px
- Max-width: 320px
- Success left border: `3px solid #22c55e`
- Error left border: `3px solid #ef4444`
- Font-size: 13px
- Auto-dismiss: 4 seconds

### Confirmation dialog (for revoke)
- Overlay: `rgba(0,0,0,0.7)`
- Card: `#111111`, border `#1f1f1f`, border-radius 10px, padding 24px
- Title: 15px/600, white
- Body: 13px, `#a1a1aa`
- Two buttons: "Cancel" (secondary) + "Revoke Token" (danger/primary)
- Focus trap the dialog while open

---

## Screen specifications

### 1. Landing page

**Navbar**
- Height: 56px
- Background: `#0a0a0a`
- Bottom border: `1px solid #1f1f1f`
- Logo left, "Login" + "Get Started" right
- "Get Started" button: primary style

**Hero**
- Centered, max-width 640px, vertical padding 80px 40px
- Headline: "Okta for AI agents" — 48px, weight 700, white, tight line-height
- Subheadline: 18px, `#a1a1aa`, margin-top 16px
- CTA buttons: side by side, margin-top 32px. Primary: "Get Started Free", Secondary: "View Docs"
- CLI code block: margin-top 48px, max-width 400px, centered

**Feature cards**
- 3-column grid, margin-top 64px
- Each card: `#111111` bg, `#1f1f1f` border, 8px radius, 24px padding
- Icon: 20px, `#22c55e`
- Title: 14px/600, white
- Description: 13px, `#a1a1aa`

### 2. Auth screen

- Full page: `#0a0a0a` bg
- Centered card: 380px wide, `#111111` bg, `#1f1f1f` border, 10px radius, 32px padding
- Logo + wordmark centered at top, 32px bottom margin
- Divider: "or continue with" in gray
- Buttons: full width, 40px height, secondary style with provider icon

### 3. Agent list (main dashboard)

**Page header row**
- Left: "Agents" title (20px/600) + agent count badge (e.g. "12 agents" in gray pill)
- Right: "Register Agent" primary button

**Table**
Columns and widths:
| Column | Width | Notes |
|---|---|---|
| Agent Name | 220px | JetBrains Mono, white |
| Owner | 180px | Email, truncated |
| Environment | 120px | Badge |
| Status | 110px | Badge with dot |
| Token Expiry | 140px | Relative time, yellow if <24h |
| Last Active | 130px | Relative time |
| Actions | 100px | Revoke button, right-aligned |

**Empty state**
- Centered vertically in table area
- "No agents registered yet" in `#a1a1aa`
- CLI snippet below: `$ scopeform deploy`

### 4. Agent detail page

**Header**
- "← Agents" back link (13px, `#a1a1aa`, hover white)
- Agent name below in JetBrains Mono (24px, white)
- Status badge next to name

**Two-column layout** (left 55%, right 45%, gap 20px)

Left: Identity card
- Rows: Name / Owner / Environment / Status / Created / Agent ID
- Each row: label (11px/500, uppercase, `#52525b`) + value (13px, `#ffffff`)
- Agent ID in JetBrains Mono with copy button

Left below identity: Scopes card
- Header: "Permitted scopes"
- Each scope: service pill + arrow + action pill
- e.g. `openai` → `chat.completions`

Right: Token card (most prominent)
- Large section, clear visual hierarchy
- "Current token" label
- Status badge (large, 24px height)
- Expiry: countdown if active ("Expires in 6h 23m"), "Expired" if not
- "Revoke Token" danger button — full width of card, 40px height

Right below token: Recent activity mini-table
- Last 5 entries only
- Columns: Time / Service / Action / Status
- "View all logs →" link below (13px, `#a1a1aa`, hover white)

### 5. Logs page

**Filter bar**
- Inline row: Agent dropdown + Status filter + Service filter + Date range
- All inputs: secondary style, 32px height
- "Clear filters" link appears when any filter is active

**Logs table**
Columns:
| Column | Width | Notes |
|---|---|---|
| Timestamp | 180px | JetBrains Mono, `#52525b` |
| Agent | 180px | JetBrains Mono, white |
| Service / Action | 220px | JetBrains Mono, `openai/chat.completions` |
| Status | 100px | ✓ Allowed (green) or ✗ Blocked (red) |

- Blocked rows: red tinted bg `#1a0505` + red left border
- Auto-refresh every 30 seconds
- "Last updated: X seconds ago" indicator (12px, `#52525b`, top right of table)
- Pagination: 50 rows/page

---

## Interaction design

### Loading states
- Use skeleton loaders for all data tables on first load
- Skeleton rows: same height as data rows, shimmer animation
- Show 5 skeleton rows while loading

### Optimistic updates
- Revoke: immediately update row status badge to "Revoked" before API responds
- Roll back if API returns an error

### Toasts
- "Token revoked for crm-agent" → success toast
- "Failed to revoke token" → error toast
- "Agent registered" → success toast

### Navigation
- Active sidebar item highlighted with left green bar
- Clicking agent name row → navigate to agent detail
- No full page reloads — use Next.js client navigation throughout

### Confirmation dialogs
- Always require explicit confirmation before revoke actions
- Dialog title: "Revoke token for [agent-name]?"
- Dialog body: "This will immediately terminate all active sessions for this agent. This cannot be undone."
- Cancel + Revoke buttons
- Default focus on Cancel (not Revoke) — prevent accidental confirmation

---

## Responsive behaviour

MVP targets desktop only (1024px+). Do not over-engineer mobile.

- Below 1024px: sidebar collapses to icon-only (40px)
- Below 768px: show a "best viewed on desktop" message — no further optimisation needed for MVP

---

## Implementation notes for Next.js

### Tailwind config additions needed
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          green: '#22c55e',
          bg: '#0a0a0a',
          card: '#111111',
          elevated: '#161616',
          subtle: '#1a1a1a',
          border: '#1f1f1f',
          'border-muted': '#2a2a2a',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    }
  }
}
```

### shadcn/ui theme overrides
When initialising shadcn/ui, override the CSS variables in `globals.css` to match the design system colors above. The default shadcn dark theme does not match — you must override every variable.

### Component file map
```
web/components/
├── layout/
│   ├── Sidebar.tsx         # Logo + nav links
│   ├── TopBar.tsx          # Org name + avatar
│   └── Shell.tsx           # Sidebar + TopBar wrapper
├── brand/
│   └── Logo.tsx            # SVG logo, accepts size prop
├── agents/
│   ├── AgentTable.tsx      # Main agents list table
│   ├── AgentRow.tsx        # Single table row
│   └── AgentEmptyState.tsx # Empty state with CLI hint
├── detail/
│   ├── IdentityCard.tsx
│   ├── ScopesCard.tsx
│   ├── TokenCard.tsx
│   └── ActivityMiniTable.tsx
├── logs/
│   ├── LogsTable.tsx
│   ├── LogRow.tsx
│   └── LogsFilterBar.tsx
└── ui/
    ├── StatusBadge.tsx     # Reusable status/env badges
    ├── RevokeButton.tsx    # Danger button + confirm dialog
    ├── SkeletonRow.tsx     # Table skeleton loader
    └── Toast.tsx           # Toast notification
```
