# 02 · Color

Token naming: `{ramp}-{stop}` primitives → semantic aliases (`surface/*`, `text/*`, `border/*`, `action/*`, `status/*`, `class/*`). **Components consume aliases only** — primitives never appear in component code.

## 1. Primitive Ramps (light-mode values)

### Ink (warm neutral — the structural ramp)
| Stop | Hex | | Stop | Hex |
|---|---|---|---|---|
| 50 | `#F4F4F6` | | 500 | `#6B7280` |
| 100 | `#EDEEF1` | | 600 | `#4B5563` |
| 200 | `#D7DAE0` | | 700 | `#3A3F4A` |
| 300 | `#B3B8C2` | | 800 | `#23262E` |
| 400 | `#8D93A0` | | 900 | `#16181D` |

### Paper (warm whites)
`0 #FFFFFF` · `50 #F7F7F5` · `100 #F1F0EC` · `150 #E9E7E1`

### Amber (brand)
| Stop | Hex | | Stop | Hex |
|---|---|---|---|---|
| 50 | `#FFFBEB` | | 500 | `#F59E0B` ★brand |
| 100 | `#FEF3C7` | | 600 | `#D97706` |
| 200 | `#FDE68A` | | 700 | `#B45309` |
| 300 | `#FCD34D` | | 800 | `#92400E` |
| 400 | `#FBBF24` | | 900 | `#78350F` |

### Functional ramps (50/100/500/600/700/900 defined; full 9 stops in tokens JSON)
- **Blue** (info/links/Trucks): 500 `#3B82F6`, 600 `#2563EB`, 700 `#1D4ED8`
- **Green** (success/On Hire/Warehousing): 500 `#10B981`, 600 `#059669`, 700 `#047857`
- **Red** (danger): 500 `#EF4444`, 600 `#DC2626`, 700 `#B91C1C`
- **Teal** (Confirmed): 500 `#06B6D4`, 600 `#0891B2`
- **Violet** (dispute/Terminals): 500 `#8B5CF6`, 600 `#7C3AED`
- **Earth** (Land & Staging): 500 `#D97706`→use `#B45309` family: 600 `#B45309`, 700 `#92400E`

## 2. Semantic Aliases (the working vocabulary)

### Surfaces
`surface/page` paper-50 · `surface/card` paper-0 · `surface/sunken` ink-100 (table stripes, wells) · `surface/raised` paper-0 + e-1 · `surface/inverse` ink-900 (nav rail, plate lockup, map callout dark) · `surface/brand` amber-500 · `surface/wash-{info|success|warning|danger|brand}` = ramp-50/100

### Text
`text/primary` ink-900 · `text/secondary` ink-700 · `text/tertiary` ink-500 (≥16px only) · `text/inverse` paper-0 · `text/on-brand` ink-900 (on amber) · `text/link` blue-700 (underlined on hover) · `text/danger` red-700 · `text/money` ink-900 + Plex Mono (money is never colored)

### Borders
`border/default` ink-200 · `border/strong` ink-300 · `border/structural` ink-900 2px (manifest total rules, tab indicators) · `border/focus` amber-500 2px outer ring + 1px paper gap · `border/error` red-600

### Actions
`action/primary` amber-500 bg + ink-900 text → hover amber-400 → active amber-600 → disabled ink-100/ink-400
`action/secondary` transparent + 1px ink-300 + ink-900 text → hover ink-50
`action/destructive` red-600 bg + paper-0 text → hover red-500 → active red-700
`action/ghost` transparent + ink-700 → hover ink-100 wash

## 3. Asset Class System (fixed, never repurposed)

| Class | `class/*` | Base | Wash | On-wash text |
|---|---|---|---|---|
| Plant & Machinery | `class/plant` | amber-600 `#D97706` | amber-100 | amber-900 |
| Trucks & Haulage | `class/trucks` | blue-600 `#2563EB` | blue-50 | blue-900 |
| Warehousing & Storage | `class/warehouse` | green-600 `#059669` | green-50 | green-900 |
| Terminals & Container Yards | `class/terminals` | violet-600 `#7C3AED` | violet-50 | violet-900 |
| Land & Staging | `class/land` | earth-700 `#92400E` | `#FDF1E7` | earth-900 |

Used in: pins, class dots, class chips, calendar row accents, dashboard class breakdowns. Plant shares the amber family with brand **deliberately** (flagship class = brand class); disambiguation comes from shape (chip vs button), never relied on color alone.

## 4. Hire Status System

| Status | Badge | Calendar block | Notes |
|---|---|---|---|
| Requested | amber-100 bg / amber-900 text | dashed amber-600 outline, amber-50 fill | tentative feel |
| Accepted | blue-50 / blue-900 + countdown | dashed blue-600, blue-50 | urgency via CountdownPill |
| Confirmed | teal-50 / teal-900 | solid teal-600 @ 20% fill, teal-600 edge | |
| **On Hire** | **solid green-600 / paper-0** | solid green-600 @ 25%, green-700 edge | the only solid badge — "live" |
| Completed | ink-100 / ink-600 | ink-200 fill | |
| Declined / Expired | outline ink-300 / ink-500 | n/a | |
| Cancelled | red-50 / red-900 | red-200 fill, struck label | |
| In Dispute | violet-50 / violet-900 + lock icon | violet-600 hatch overlay | freezes UI actions |

## 5. Dark Mode (specified now; ships post-MVP)

Inversions are token-level only — components untouched. `surface/page` ink-900 · `surface/card` ink-800 · `surface/sunken` `#101216` · text ramps invert (primary paper-50, secondary ink-300) · borders ink-700/600 · **amber-500 stays amber-500** (passes on ink-900) · washes become `ramp-900 @ 30%` with `ramp-200` text · class/status hues shift to their 400 stops for dark-surface contrast · map: no dark style in MVP (map stays light; app chrome around it darkens).

## 6. Data Visualization (dashboard & analytics)

Categorical order: amber-500 → blue-600 → green-600 → violet-600 → ink-400 (≤5 series; beyond 5, redesign the chart). Class-based charts use class hues. Single-series = amber-500 bars/lines on ink-100 grid (0.5px gridlines), Plex Mono axis labels 12px, no 3D/area gradients/donuts (bar, line, simple stacked only). Positive/negative deltas: text +/− prefixes in green-700/red-700 — arrows optional, color never alone.

## 7. Contrast Budget (enforced in review)

- Text: ≥4.5:1 always; large display numerals ≥3:1 permitted at ≥28px/500.
- `amber on paper` is **forbidden for text** at any size (3.0:1) — amber text only on ink-900/800.
- Status washes: text uses the ramp's 900 stop — every pair above pre-verified.
- Interactive affordances ≥3:1 against adjacent surface (borders/icons).
- Sunlight rule of thumb: if a token pairing only just passes AA, it fails Terminal — prefer the next stop up.
