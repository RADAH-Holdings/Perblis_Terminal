# 06 · Domain Components
Terminal-specific composites. These are the screens' load-bearing parts; each maps to FSD behaviour.

## 1. Trust Layer

### VerifiedBadge (accounts) & TierBadge (listings)
- Account: `Basic` ink-300 outline circle-check · `Verified` blue-600 check · `Business Verified` blue-600 filled shield. Always icon+label first occurrence per screen, icon-only after (tooltip/long-press reveals label).
- Listing tier: same geometry — `Basic` ink-400 · `Verified` blue-600 · `Inspected` amber-600 filled with star-check. Placement: after supplier name / on listing card top-right over photo (on scrim).
- Never adjacent to status badges without s-2 separation; never green.

### LockedTerms (Manifest Block M2)
Two strictly separated variants (D-014 — the fee is supplier-confidential):
- **Supplier variant:** Hire value → Service fee (with `fee_basis` caption: "10% weekly · min ₦2,500") → **You receive** (2px ink-900 rule above, mono-lg).
- **Hirer variant:** dates/duration rows → **You pay** (total, mono-lg). No fee line, no payout line, no fee footnote — the hirer sees one figure and it is exactly what they pay.
Shared: pre-acceptance header "Estimated terms" + ink-500 caption "Final at acceptance"; locked state adds lock icon + "Terms locked 12 Jun 2026, 14:32" caption.

### EventTimeline
Vertical stepper: node (status-colored 10px dot; current pulses once on load) · timestamp `mono-sm` · actor + transition text body-sm ("Supplier accepted · terms locked") · connecting 2px ink-200 rail. Collapsible beyond 5 events ("Show all 12"). Same component renders in Ops with raw metadata expandable per node.

### MaskedContact
Inline chip within message text: `0803••• ` + lock 12px, amber-100 bg, amber-900 text. First occurrence per conversation appends explainer row (banner-info style): "Numbers unlock after payment — Terminal protects both parties. [Why?]". Post-payment: chips render plain text. Never red, never shame copy.

## 2. Cards

### ListingCard
Photo 4:3 (skeleton ink-100; camera-off glyph fallback) with class chip top-left + tier badge top-right + distance pill bottom-right (map contexts) · title body 500 2-line clamp · spec headline caption ink-500 (★ spec + yard name + supplier badge) · price row: `mono-lg` + `/day` + availability caption ("6 of 8 units free" green-700 / "Unavailable selected dates" red-700). Variants: `map-preview` (horizontal, in pin callout/bottom sheet), `grid` (portal/app browse), `row` (portal tables context).

### YardCard
Squircle logo 40px (initials fallback) + verified tick on border · name h3 + supplier caption · class dots row (≤3 + overflow count) · `12 assets` mono + distance pill · chevron. Tap → Yard Sheet (app) / yard filter (portal).

### HireCard
Listing thumb 56px squircle-r-md · title + dates (`mono-sm`: `12 Jun → 26 Jun · 14 days`) · StatusBadge · amount mono right · context strip: CountdownPill when Accepted (payment deadline), "Action needed" amber dot when Requested (supplier view), handover prompt when start/end imminent.

## 3. Map System
- **Base style "Terminal Chart":** OpenFreeMap Liberty customized — land paper-50 tint, water `#C6D2D9` desaturated, roads ink-300/400, POI labels off below z14, no default POI icons (our pins are the only color). Style JSON in `packages/tokens/map/`.
- **AssetPin:** 32px teardrop class-color fill, paper-0 class glyph, 1px ink-900 ring; selected: scale 1.2 + amber ring + e-1.
- **YardPin:** 40px squircle supplier logo / ink-900+amber initials · amber-500 count badge (ink-900 text) top-right · ≤3 class dots beneath (paper-0 ring each) · blue tick on border when Verified · filtered: badge shows matching count; zero-match = whole pin 40% opacity (never removed) · selected: amber 2px ring + callout.
- **Cluster:** 36px ink-700 circle, paper-0 mono count — deliberately drab; tap = zoom-in (max-zoom: spider-fan for distinct-owner coincident pins, FSD E2).
- **Pin callout (web/portal pickers):** e-1 card with map-preview ListingCard.
- **Controls:** locate-me FAB-style 44px paper-0 circle bottom-right above sheet · radius control inside filter sheet · attribution per OpenFreeMap/LocationIQ requirements, caption ink-400.
- **States:** tiles loading = paper-100 grid shimmer; tile failure = banner + auto-switch to list view (FSD degradation).

## 4. CalendarGantt (portal)
Yard group headers (overline + class dots) · rows = listings (compact 40px), row header: title + `6/8` utilisation fraction mono + mini-bar (green-600 fill ratio) · columns = days (today: amber hairline + label) · blocks per status (02 §4): solid = confirmed/on-hire, dashed = requested/accepted, hatch = dispute; block label: hirer name caption, truncates to initials <64px · drag = none (read-only MVP) · click → hire detail · horizontal virtualized scroll, month jump, weekend columns paper-100.

## 5. Availability & Booking widgets
- **AvailabilityStrip (listing detail):** next-60-days micro-calendar: 6px day cells, green-100 free / ink-200 held; legend caption.
- **PricePreview (request flow):** live Manifest block recomputed per date change; duration classification line: "14 days → 2 × weekly — best price ✓" caption green-700 with alt-scheme strikethrough (`₦1,050,000` ink-400) when best-price beats naive daily — the rule made visible (D-008).
- **CountdownPill:** `mono` `3:42:10`, blue-50/blue-900 → red-50/red-900 under 30min + pulse; expired → "Window expired" ink badge.

## 6. Handover
**HandoverCapture (app):** full-screen camera, checklist overlay chips per class recipe (03 §7 FSD — "Front ✓ · Rear · Meter"), thumbnail rail, reading input (mono numeric pad) when class requires, notes, then **ConfirmPanel**: both-party state ("You confirmed · Waiting for supplier" with avatar ticks). **HandoverRecord (read):** photo grid 2×2 + reading + timestamps + confirmations — renders as evidence card in hire detail and disputes.

## 7. Conversations
Thread row: counterparty avatar + name + verified tick · listing thumb 40px + title caption + yard caption · last message preview 1-line · timestamp `mono-sm` · unread badge. Message bubbles: sender paper-0 + 1px border (right), receiver ink-100 (left), r-md with 4px tail-corner; body 16px; timestamp+read tick caption below group; date separators overline; system messages (status changes) centered caption with status dot — the conversation doubles as a light timeline. Composer: 48px input + send (primary icon button); attachment button hidden in MVP (text-only chat, photos live in handover/listing flows).

## 8. Receipt (brand artifact, 01 §6)
Layout: plate lockup header + hire ID `mono` · PAID stamp (M3, −6°) overlapping header rule · manifest ledger (hirer-facing variant) · dates/listing/yard block · QR (ink-900) deep-link → hire · perforated edge (8px dash) footer with NDPR caption + support contact. Renders: app share-image (1080×1350 export), portal print CSS, email HTML (table-based, same tokens). Stamp colors: PAID amber · REFUNDED ink · COMPLETED green-600.

## 9. Ops Console accents
Django Admin stays stock-functional, with a thin brand layer only: hazard stripe 4px under the header, plate lockup, amber primary buttons, status colors in list filters. Queues use standard changelist + custom actions (TSD §3) — no bespoke UI investment in MVP beyond the dashboard template (stat cards + class breakdown using data-viz rules 02 §6).
