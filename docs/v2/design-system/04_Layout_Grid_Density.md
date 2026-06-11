# 04 · Layout, Grid, Density & Elevation

## 1. Spacing Scale
4px base: `s-1 4 · s-2 8 · s-3 12 · s-4 16 · s-6 24 · s-8 32 · s-12 48 · s-16 64`. Vertical rhythm between sections: s-8 portal, s-6 app. Card padding s-4; dense table cells s-2/s-3.

## 2. Supplier Portal Grid
- **Frame:** fixed ink-900 nav rail 240px (collapsible to 64px icon rail) + content region max-width 1320px, centered, gutter 24px.
- **Grid:** 12-col, 24px gutters. Standard recipes: dashboard stats 4×3-col; tables full-width; detail pages 8-col main + 4-col side panel (financials/chat); forms single 6-col column left-aligned (never centered).
- **Breakpoints:** `xl ≥1280` full · `lg 1024–1279` rail collapses · `md 768–1023` side panels stack under main · `sm <768` portal is *functional-not-optimized*: tables become card lists, calendar gains horizontal scroll. (Desktop-first per FSD; tablet is the supported floor.)
- **Sticky:** table headers, detail action bars (bottom), calendar date header.

## 3. Hirer App Layout
- **Frame:** edge-to-edge map; all other screens 16px gutters, max content 480pt.
- **Stack:** single column; 2-col only for stat pairs and photo grids.
- **Bottom sheet snap points:** peek 88pt (pin preview) · half 50% (Yard Sheet) · full 92% (filters, sheet expanded). Tab bar 56pt + safe-area; FAB-free system (primary actions live in context, not floating).
- **Thumb rule:** primary action always within bottom 40% of screen on transactional flows.

## 4. Density Modes (portal)
`comfortable` (default): rows 52px, body-sm text. `compact` (user toggle, persisted): rows 40px, mono-sm figures — built for the 40-listing supplier. Token pair `density/row-height`, `density/cell-pad` switch; nothing else may vary.

## 5. Elevation & Layering
Borders carry structure; shadow = "above the page" only:
- `e-0` flat + border (cards, tables, manifest blocks)
- `e-1` `0 2px 8px ink-900 @ 10%` (dropdowns, popovers, pin callouts)
- `e-2` `0 8px 24px ink-900 @ 16%` (modals, bottom sheets, command palette)
- Z-order: content < sticky bars < nav < sheet/scrim < modal < toast. Scrim: ink-900 @ 40%.

## 6. Page Anatomy Recipes
- **Portal screen:** breadcrumb (caption, ink-500) → h1 + primary action right-aligned → filter row → content → sticky action bar (detail pages only).
- **App screen:** nav header 56pt (title centered, back left, overflow right) → content → bottom action zone. Map screen inverts: floating search pill + filter chips over map, no header.
- **Hairline discipline:** dividers are `0.5px ink-200`; full-bleed in lists, inset s-4 inside cards. Max one nested border level (no boxes-in-boxes-in-boxes).
