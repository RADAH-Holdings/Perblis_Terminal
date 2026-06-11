# 03 · Typography

## 1. Faces & Roles

| Role | Face | Weights | Where |
|---|---|---|---|
| **Display** | Archivo | 600, 700; Expanded 600 for lockups | Headings, stat numerals' labels, stamps, nav wordmark |
| **Text** | Inter | 400, 500, 600 | All UI chrome, body, forms, badges |
| **Data** | IBM Plex Mono | 400, 500 | Money, specs, IDs, dates-in-tables, OTP, coordinates, countdowns |

All self-hosted (`next/font` / Expo `useFonts`); fallback stacks: Archivo→`system-ui bold`, Inter→`system-ui`, Plex Mono→`ui-monospace`. Inter loaded with `tnum, calt` features on; `ss01` off.

## 2. Scale

| Token | Size/Line | Face/Weight | Use |
|---|---|---|---|
| `display-xl` | 40/44 | Plex Mono 500 | Dashboard hero figures, price headers |
| `display-lg` | 32/38 | Archivo 700 | Marketing/onboarding headlines |
| `h1` | 28/34 | Archivo 600 | Screen titles |
| `h2` | 22/28 | Archivo 600 | Section heads |
| `h3` | 18/24 | Archivo 600 | Card titles, panel heads |
| `body-lg` | 17/26 | Inter 400 | Long-form (policies, descriptions) |
| `body` | 16/24 | Inter 400/500 | Default UI text |
| `body-sm` | 14/20 | Inter 400/500 | Secondary rows, table cells (portal) |
| `caption` | 13/18 | Inter 500 | Labels, badges, timestamps — **portal floor** |
| `mono-lg` | 20/26 | Plex Mono 500 | Card prices, locked-terms total |
| `mono` | 15/22 | Plex Mono 400/500 | Spec values, table figures, IDs |
| `mono-sm` | 13/18 | Plex Mono 400 | Dense table figures, coordinates |
| `overline` | 12/16 | Archivo 600, +10% tracking, caps | Manifest headers, stamp labels — **the only 12px and only all-caps style** |

**App floor: 14px** (caption promotes to 14/20 on mobile). Responsive: h1/h2 drop one step ≤360px width devices.

## 3. Money Typesetting (normative)

- Face: Plex Mono 500 always; ₦ + thin space + grouped: `₦1,250,000`. Kobo never displayed.
- Sizes: card price `mono-lg` with `/day` unit in Inter `caption` ink-500; detail/locked-terms total `display-xl` or `mono-lg` per context; tables `mono` right-aligned, columns aligned on the decimal-less digit grid.
- Abbreviation `₦1.25M` permitted **only** on map pin callouts and dashboard deltas; full value always within one tap/click.
- Negative amounts: `−₦90,000` (true minus U+2212), never red-colored, never parentheses.
- Countdown: `mono` `H:MM:SS`, blue-700 → red-700 at <30:00.

## 4. Composition Rules

- Max two faces per view region; Archivo never set below 16px; Plex Mono never used for sentences.
- Line length: 60–75ch long-form; UI labels ≤3 words where possible (verbs first — 09 Content).
- Truncation: titles 2-line clamp with ellipsis; **figures, dates, and IDs never truncate** — layouts must reserve room (that's the layout's bug, not the number's).
- Sentence case everywhere except `overline` tokens and stamps. No italics in UI (reserved for citation in legal pages). Underline = links only.
- Letter-spacing: 0 default; Archivo display −1%; overline +10%.
