# 03 · Supplier Portal — Screen Specifications
Frame: ink-900 nav rail (05 §5) + content region (04 §2). Density toggle global. All tables = DataTable spec; all money mono right-aligned.

## P1 · Auth & Onboarding
Sign-in/register split-screen: form left, duotone port photography right (the portal's one cinematic moment). OTP inline. Post-register: role intent → dashboard with **onboarding checklist** card (5 items, progress bar, per-item CTAs; collapses when complete — J1).

## P2 · Dashboard `/dashboard`
- **Stat row (4):** Earned this month (display-xl mono + delta) · On hire now (n/total + utilisation caption) · **Action needed** (amber wash card: pending requests with nearest expiry countdown) · Unread messages. Each card → filtered destination.
- **Payout strip:** "₦810,000 queued — payouts run weekly" + last payout reference (F11).
- **Activity feed:** last 10 events (EventTimeline rows, cross-hire) with deep links.
- **Per-yard segmentation** when >1 yard: stat row gains yard tabs (J6).
- States: checklist-dominant (new) · empty feed ("activity appears here") · all-zero stats show em-dash not ₦0 (avoid "failing business" feel on day one).

## P3 · Assets `/assets`
Toolbar: search · filters (status, class, yard, price) · group-by-yard toggle · density · `Add asset`. Columns: photo+title · class chip · yard · status badge · price/day mono · units (6/8 mini-bar) · active hires · created. Row actions: edit, duplicate, pause/unpause (undo-toast), archive. Bulk: pause, archive, assign-to-yard. Empty: "List your first asset" EmptyState. Status copy on hover explains visibility ("Paused — hidden from the map").

## P4 · Asset Form `/assets/new`, `/assets/:id`
Six-step Stepper (per-step save, draft chip in header):
① Class & type (class cards with glyphs → type select) ② Details & specs (template-driven: required fields gate Next; completeness meter caption) ③ Pricing & units (daily required; weekly/monthly with "set these to win longer hires" nudge + PricePreview sample; unit stepper + optional labels) ④ Photos (grid uploader per 07 §9, cover star, min 1) ⑤ Location (yard chips first — "or drop a new pin"; map picker w/ LocationIQ search; "save as yard" toggle) ⑥ Review (full preview as hirers see it + publish gates checklist).
Publish-blocked states named (F9). Edit mode: same form, banner if active hires exist ("changes don't affect locked terms").

## P5 · Yards `/yards`
Card grid: mini-map, name, address, asset count, edit/rename. Create modal: name + search/pin map. Delete only when empty (explain). Auto-yard prompts surface here as suggestions ("3 listings cluster near Apapa — create a yard?").

## P6 · Hires `/hires`
Tabs: **Needs response** (Requested, expiry countdown column, amber) · Upcoming (Accepted+Confirmed) · On hire · History. Columns: listing · hirer (+VerifiedBadge) · dates mono · duration · hire value · **your payout** mono · status. Filters: listing, yard, class, date range. Row → P7. Bulk: none (decisions are individual — deliberate).

## P7 · Hire Detail `/hires/:id`
8+4 layout (04 §2): main = status banner + listing snapshot + dates + EventTimeline + HandoverRecords; side panel = **LockedTerms (supplier variant: "You receive" hero — the full fee breakdown lives here and only here, D-014)** + hirer card (level, completed hires count, member since) + conversation panel (live, embedded composer).
Action bar (sticky, state-dependent): Accept (w/ acknowledgment when applicable) / Decline (reason dialog) · Cancel (refund preview + evidence note) · Confirm handover · Raise issue. Every machine state has its banner + permitted actions matrix (mirrors FSD §6.3 exactly — UI cannot offer an illegal transition).

## P8 · Calendar `/hires/calendar`
CalendarGantt per 06 §4: yard group headers, listing rows with unit utilisation, month nav + today jump, status legend, weekend tint. Click block → P7; click empty cell → nothing (read-only MVP, tooltip "availability is set by hires"). Pending blocks dashed. Export: none MVP.

## P9 · Messages `/messages`
Two-pane: thread list (06 §7 rows, filter: all/enquiries/hires) + conversation pane (same anatomy as app S15, MaskedContact identical). Hire-bound threads show summary side-strip (dates, status, LockedTerms mini). Keyboard: ↑↓ thread nav, Enter to focus composer.

## P10 · Storefront `/storefront`
Preview-as-hirer (live render) + edit drawer: cover image, about, logo. "Share storefront" copies public URL (slug reserved per Lexicon). Verification badge state shown with upgrade CTA (CAC → Business Verified).

## P11 · Settings `/settings`
Sections: Personal (name, phone, photo) · Business profile · **Bank details** (masked display, edit re-auth with password, encryption note caption) · Notifications (email toggles per event) · Verification (status + documents + resubmit) · Account (password, delete w/ 30-day + active-hire guard) · Legal.

## P12 · System
404 / 500 (illustration + Sentry ref) · suspended (support) · session-expired re-auth modal preserving route (F12) · maintenance flag page.

---
**Coverage check:** FSD §8.2 routes fully mapped (P1–P12); supplier journeys J1/J4/J6 walkable end-to-end; every supplier-side hire action has exactly one home (P7 action bar).

## Stage-6 build review checklist (applies to every screen, both surfaces)
1. Components referenced exist in design-system 05/06 — no orphan UI
2. All 7 data states designed: ideal · empty · loading · partial · error · offline · forbidden
3. Copy from 09 catalogs; status vocab table is the only status language
4. Deadlines surfaced in all three mandatory places (07 §10)
5. Money figures mono, full-value, source = LockedTerms fields — never recomputed client-side
6. One motif max; contrast budget respected; touch targets ≥48dp app / ≥40px portal
