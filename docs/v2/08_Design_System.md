# Terminal v2 — Stage 5: Design System (Executive Summary)
**"Heavy Duty"** — the visual and interaction language for the Supplier Portal + Hirer app
v1.0 · June 2026 · Implements FSD v2.0 surfaces (§8) · Feeds Stage 6 (UX/screens)

> **This file is the executive summary.** The full, expanded system lives in [`design-system/`](design-system/00_Index.md) — 10 chapters covering brand foundations & signature motifs, complete color ramps + dark mode, full type scale, layout/grid/density, core components with state matrices, domain components (trust layer, map, calendar, receipt), patterns (empty/error/onboarding/notifications), motion, microcopy catalogs, and token architecture/governance. Where this summary and the chapters differ, **the chapters win.**

---

## 1. Design Direction

### 1.1 Personality
Terminal's aesthetic is **industrial utility**: the confidence of a well-run port, not the gloss of a consumer app. Reference points are shipping manifests, equipment data plates, safety signage, and contract documents — surfaces this market already trusts. Three words that gate every visual decision: **Legible. Sturdy. Verifiable.**

What this means concretely:
- **High contrast, always.** Site managers use this app outdoors at noon. If it fails the sunlight test, it fails.
- **Squared, not soft.** Tight corner radii, visible 1px borders, structural dividers. Bubbly = consumer = wrong market.
- **Numbers are the heroes.** Prices, tonnage, TEU, distances — set in mono, tabular, never truncated. The spec sheet *is* the brand.
- **Trust is rendered, not implied.** Verification badges, locked-terms callouts, event timelines, and masked-contact notices get first-class visual treatment — they're the product (01 §3).
- **No decoration without information.** Every color carries meaning (class, status, action). Illustration is limited to empty states.

### 1.2 Anti-goals
Generic SaaS gradient-blue; rounded-everything friendliness; thin grey 12px text; emoji in UI copy; stock photos of smiling people in hard hats.

## 2. Foundations (Tokens)

Tokens live in `packages/tokens` (JSON → Tailwind config for portal, TS constants for app). Names below are canonical.

### 2.1 Color

**Core palette**

| Token | Hex | Use |
|---|---|---|
| `ink-900` | `#16181D` | Primary text, headers, footers |
| `ink-700` | `#3A3F4A` | Secondary text |
| `ink-500` | `#6B7280` | Tertiary text, placeholders (smallest text ≥16px at this contrast) |
| `ink-200` | `#D7DAE0` | Borders, dividers |
| `ink-100` | `#EDEEF1` | Subtle fills, table stripes |
| `paper-0` | `#FFFFFF` | Cards, sheets |
| `paper-50` | `#F7F7F5` | App/page background (warm off-white, not blue-grey) |
| **`amber-500`** | `#F59E0B` → brand ramp 600 `#D97706` | **Brand primary** — safety amber. Primary buttons (with ink-900 text), active states, brand moments |
| `amber-100` | `#FEF3C7` | Amber wash (highlights, pending fills) |
| `accent-ink` | `#16181D` on amber | Brand lockup: amber on ink / ink on amber, like plant livery |

Safety amber is the construction industry's own color — visible, urgent, and instantly at home on a yard. Paired with near-black ink it gives Terminal the look of equipment livery (CAT, JCB, Hilti all live in this space) while remaining ownable through composition rather than hue.

**Asset class hues** (pins, dots, chips — fixed, never repurposed)

| Class | Token | Hex |
|---|---|---|
| Plant & Machinery | `class-plant` | `#D97706` (amber-600) |
| Trucks & Haulage | `class-trucks` | `#2563EB` (blue) |
| Warehousing & Storage | `class-warehouse` | `#059669` (green) |
| Terminals & Container Yards | `class-terminals` | `#7C3AED` (violet) |
| Land & Staging | `class-land` | `#B45309` (earth brown) |

**Hire status colors** (badges, calendar blocks, timeline)

| Status | Token | Hex | Fill style |
|---|---|---|---|
| Requested | `status-requested` | `#D97706` | amber-100 wash + amber text |
| Accepted (awaiting payment) | `status-accepted` | `#2563EB` | blue wash + countdown affordance |
| Confirmed | `status-confirmed` | `#0891B2` | teal wash |
| On Hire | `status-onhire` | `#059669` | solid green badge — the "live" state |
| Completed | `status-completed` | `#6B7280` | grey wash |
| Declined / Expired | `status-ended` | `#6B7280` | grey outline |
| Cancelled | `status-cancelled` | `#DC2626` | red wash |
| In Dispute | `status-dispute` | `#9333EA` | purple wash + lock icon |

**Semantic:** `success-600 #059669` · `danger-600 #DC2626` · `warning-600 #D97706` · `info-600 #2563EB`. Money-positive amounts are never green-coded (money is neutral ink; *status* is colored).

### 2.2 Typography

| Role | Face | Notes |
|---|---|---|
| **Display / headings** | **Archivo** (SemiBold/Bold; Expanded for brand lockups) | Industrial grotesque; free (OFL). H1 28/34, H2 22/28, H3 18/24 |
| **UI / body** | **Inter** (400/500/600) | Body 16/24 portal · 16/22 app; small 14/20 — **nothing below 13px ever**; `tnum` on wherever digits align |
| **Data / money / refs** | **IBM Plex Mono** (500) | ALL monetary amounts, spec values, hire IDs, dates in tables, OTP digits. The data-plate voice. |

Money setting rules: `₦` + thin space + grouped digits (`₦1,250,000`), Plex Mono, never abbreviated in transactional contexts ("₦1.25M" allowed only on map pins/cards, full value on detail+confirm screens). Kobo never shown (whole-naira product).

### 2.3 Space, shape, depth
- **Spacing:** 4px base scale (4/8/12/16/24/32/48/64). Cards pad 16; screens gutter 16 (app) / 24 (portal).
- **Radius:** `r-sm 4` (inputs, chips) · `r-md 8` (cards, sheets) · `r-lg 12` (modals, bottom sheet top) · `r-full` only for avatars + count badges. **Yard pin squircle: r-md on a 40px tile.**
- **Borders over shadows:** default card = `1px ink-200` + `paper-0`, no shadow. Elevation reserved for overlays: `e-1` (dropdowns) and `e-2` (sheets/modals) only.
- **Touch targets:** ≥48×48dp app; ≥40px portal. Hit-slop on map pins +8.

### 2.4 Iconography & imagery
- **Lucide** icon set (portal + RN), 1.75px stroke, ink-700 default — utilitarian, free, identical cross-platform.
- **Asset class glyphs** (the 5 pin icons): custom 16px solid glyphs — excavator silhouette, truck, warehouse, container stack, surveyed-plot. Drawn once as SVG in `packages/tokens/glyphs`; used on pins, chips, class pickers, empty states.
- Photography: supplier-uploaded only. 4:3 thumbnails, 16:10 gallery; `ink-900 @ 40%` gradient under any text-on-photo. Empty-state illustration: single-color line drawings in ink-300 + amber accent (no character mascots).

### 2.5 Motion
Functional only: 150ms ease-out micro (press, chips), 250ms standard (sheets, accordions), 350ms map camera. Status changes announce with a single amber pulse on the badge (no confetti — a paid hire celebration is the **receipt**, rendered like a stamped document). Respect `prefers-reduced-motion` / RN reduce-motion.

## 3. The Trust Layer (first-class components)

These four patterns ARE the product and get system-level definitions:

1. **VerifiedBadge** — three rungs: `Basic` (ink outline) · `Verified` (blue check) · `Business Verified` (blue filled shield). Listing tiers reuse the geometry in grey/blue/gold (`Inspected`). Always icon+label at first occurrence per screen, icon-only thereafter. Never adjacent to unrelated green/success UI.
2. **LockedTerms panel** — the financial terms rendered as a bordered "document block": Plex Mono figures, hairline rules, lock glyph + "Terms locked at acceptance" caption once locked. Two audience-separated variants (D-014): supplier sees Hire Value / Service Fee / You Receive; **hirer sees only "You pay" — fee and payout figures never render on hirer surfaces.** Identical anatomy on app, portal, and receipt email.
3. **EventTimeline** — the hire event log as a vertical stepper: timestamp (mono) + actor + transition, statuses in their colors. Same component renders disputes evidence view in Ops.
4. **MaskedContact notice** — inline redaction chip: `0803••• 🔒` + one-line explainer + "Unlocks after payment". Styled as informative (ink+amber), never punitive (red).

## 4. Component Inventory

### 4.1 Shared semantics (portal + app)
Buttons (primary amber/ink, secondary outline, destructive red, ghost; loading = spinner replaces label, width locked) · Inputs (1px ink-200, focus = 2px amber, error = red + 14px message; labels always visible — no placeholder-as-label) · Select/Chips (class chips carry class dot) · StatusBadge (table above) · ListingCard (photo 4:3, class chip, title 2-line, spec headline ★, price-from mono, distance, badge) · YardCard (logo squircle, name, supplier, count, class dots, distance) · HireCard (listing thumb, dates mono, StatusBadge, amount, deadline countdown when Accepted) · PriceBreakdown = LockedTerms panel · SpecTable (label/value rows, mono values + units, zebra ink-100) · EmptyState (glyph + one sentence + one action) · Toast/Banner (info amber-wash, error red-wash; banners for window countdowns).

### 4.2 Map language (app-first; portal yard pickers reuse)
- **Base style:** OpenFreeMap *Liberty* customized: desaturated land (`paper-50` tint), ink roads, water `#B8C4CC` — the map recedes, pins carry the color.
- **Asset Pin:** 32px teardrop in class color, white class glyph, ink-900 1px ring; selected = +20% scale + amber ring.
- **Yard Pin:** 40px squircle — supplier logo (or 2-letter initials on ink-900), **amber count badge** top-right (matching count when filtered; 40% opacity whole-pin when zero-match), ≤3 class dots beneath, blue check on border when supplier Verified.
- **Cluster:** 36px neutral circle, `ink-700` fill, white count — visually *boring on purpose* (semantic yards must outshine spatial clusters).
- **Distance chip:** `4.3 km` mono on paper-0 pill, attached to cards and pin callouts.

### 4.3 Portal-specific
DataTable (sortable, filter row, bulk-select, sticky header, mono numerics right-aligned) · CalendarGantt (yards as group headers, listings as rows, day columns; blocks in status colors, pending = dashed amber outline, unit-utilisation bar `6/8` in row header) · Stepper (6-step listing form, amber progress) · DashboardStat (label + mono figure + delta) · QueueRow (Ops: verification/payout/reports with inline actions) · SideNav (ink-900 rail, amber active indicator, Archivo wordmark).

### 4.4 App-specific
BottomSheet (Yard Sheet, filters; r-lg top, drag handle, 50%/92% snap points) · FilterBar (horizontal class chips over map, paper-0 pills) · TabBar (5: Map · Search · Hires · Messages · Profile; amber active) · DatePicker (range; unavailable dates struck in ink-200, holds in amber-100) · CountdownPill (payment window mm:ss, blue→red under 30min) · HandoverCapture (camera-first frame with photo checklist overlay) · OTPInput (6 mono cells) · ReceiptCard (stamped-document style: perforation edge, mono ledger, share-as-image).

## 5. Voice & Copy Rules
British English, industry vocabulary (per Lexicon — *enquire, hire, plant, yard, off-hire*). Sentences ≤ 12 words in UI chrome. Numbers and dates: `12 Jun 2026`, `14:30`, `12.4 km`, `22 t`, `450 TEU`. Buttons are verbs ("Request to Hire", "Accept hire", "Confirm handover"). Errors say what happened + what to do, never codes alone. Money copy is contractual and audience-separated (D-014): hirer — "You'll pay ₦900,000."; supplier — "You receive ₦810,000 after Terminal's service fee."

## 6. Accessibility & Environment
WCAG 2.2 AA contrast minimum (amber-on-ink and ink-on-amber both pass; amber text on white is **forbidden** — amber is fill/accent only) · smallest text 13px portal / 14px app · all status conveyed by color + label/icon (never color alone) · screen-reader labels on pins ("Yard: BNN Apapa, 12 assets, 4.2 kilometres") · keyboard-complete portal (calendar included) · low-bandwidth: photo lazy-load with ink-100 skeletons, map degrades to list view on tile failure.

## 7. Theming & Implementation
- Light theme only at MVP (dark mode = post-MVP; tokens already namespaced to allow it). Map has no dark variant in MVP.
- **Portal:** tokens → Tailwind theme + shadcn/ui CSS variables (`--primary: amber-500`, radius overrides to r-sm/md). shadcn components restyled, not reinvented.
- **App:** tokens → TS constants consumed by NativeWind (Tailwind-for-RN) for 1:1 class parity with portal; custom components per §4.4.
- Fonts bundled (Expo `useFonts` / portal `next/font` self-hosted — no external font CDN).
- `packages/tokens` is the single source: JSON definitions + build script emitting `tailwind.tokens.js`, `tokens.ts`, `glyphs/*.svg`.

## 8. Sign-off
1. ✅/❌ Direction: industrial utility, safety-amber + ink identity (§1–2.1)
2. ✅/❌ Type stack: Archivo / Inter / IBM Plex Mono, money-setting rules (§2.2)
3. ✅/❌ Class + status color assignments (§2.1)
4. ✅/❌ Trust layer as first-class components (§3)
5. ✅/❌ Map visual language (§4.2)
6. ✅/❌ Implementation route: shared tokens package, shadcn + NativeWind (§7)
