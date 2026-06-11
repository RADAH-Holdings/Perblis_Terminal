# 07 · Patterns
Recurring multi-component behaviours. Every screen in Stage 6 references these by name.

## 1. Empty States
Anatomy: illustration (01 §5, 96–128px) · h3 one-liner · body-sm cause/benefit (≤2 lines) · one primary action · hazard-stripe baseline (M1) 40% opacity. Catalog:
| Context | Headline | Action |
|---|---|---|
| Map, no results in view | "Nothing here yet" | "Widen search" (resets radius) |
| Assets, new supplier | "List your first asset" | "Add asset" |
| Hires (hirer) | "No hires yet" | "Explore the map" |
| Messages | "No conversations" | — |
| Verification pending | "Documents under review" + SLA copy | — |
| Search, no match | "No matches for ‘crane lagos island'" | "Clear filters" |
Empty ≠ error: empty states never use warning/danger colors.

## 2. Loading
Skeletons mirror real anatomy (05 §4); map uses tile shimmer; **perceived-speed rules:** cached-first render (TanStack), optimistic UI only for messages (send → grey tick → confirmed tick) and read-states — never optimistic for money or hire transitions (webhook truth, TSD §3.6). Stale-while-revalidate badge: subtle "Updated 2 min ago" caption on dashboards.

## 3. Errors & Offline
- **Field errors:** 05 §2. **Screen errors:** illustration + "Something broke on our side" + retry + Sentry ref `mono-sm`.
- **Offline (app):** persistent ink-900 banner "Offline — showing saved data"; mutations disabled with explanatory toast; auto-retry on reconnect.
- **Payment failures:** never generic — Paystack reason mapped to plain copy + remaining attempts + countdown still visible (09 catalog).
- **Conflict (409 from availability race):** "Those dates were just taken" sheet with refreshed AvailabilityStrip + nearest-free suggestion.

## 4. Onboarding
- **Hirer (app):** 3 screens max — value prop (map duotone hero) → OTP → optional "verify now or later" (skippable, banner persists). Location permission asked **in context** (first map open, with pre-prompt explaining why).
- **Supplier (portal):** checklist pattern on dashboard until complete: Business profile → Bank details → First yard → First listing → Verification. Progress bar amber; dismissible per item, never fully hidden until done.
- Role activation (hirer→supplier in app): handoff screen — "Continue on your computer" + emailed magic link to portal (portal is the supplier surface; app explains rather than half-implements).

## 5. Notifications (in-app + email)
- In-app: badge counts (nav) + activity feed rows (dashboard) + toast for live events while in-app (Ably).
- Email (Resend, manifest-styled templates): triggers = hire requested (→supplier), accepted+payment link (→hirer), paid (→both, receipt), declined/expired/cancelled (→affected), payout sent (→supplier), verification result (→user). Subject pattern: `[Terminal] {event} — {listing title}`. Every email's primary CTA deep-links to the exact record.
- Quiet rule: one email per event, no digests in MVP except founder's weekly ops digest.

## 6. Destructive & Irreversible Actions
Two-step always: action → confirm dialog naming the object ("Cancel hire #T-2941? The hirer will be refunded ₦900,000"). Type-to-confirm reserved for Ops only (remove listing, suspend user). Post-payment cancellations show refund math **before** confirm (refund preview = Manifest block). Undo-toast pattern for reversible-in-grace actions (pause listing, archive draft) — 6s window.

## 7. Permissions & Gating
- Guest hits protected action → auth sheet ("Sign in to request this hire") preserving intent (post-auth deep-back to the action).
- Basic account hits ₦250k cap → gate sheet: cap explanation + "Verify identity" CTA + SLA promise (FSD §4.1).
- Unverified supplier tries publish → checklist redirect (this pattern, not an error).

## 8. Search & Filtering
Filter state is **visible, countable, and clearable**: chips row shows active filters with counts ("Plant · ≤₦100k/day · 25km ✕"); result count always on screen ("34 assets"); map/list toggle preserves state; "Clear all" after ≥2 filters. Saved searches: post-MVP (slot reserved in sheet).

## 9. Photography Capture & Upload
Used in listings + handover: client-side resize (1920px/≤1MB) → presigned PUT → progress per photo (linear bar on thumb) → retry per-item on failure (never all-or-nothing) → drag-reorder (portal) / long-press reorder (app) → cover star. Upload errors name the cause ("Too large — max 10MB").

## 10. Countdown & Deadline Surfaces
Deadlines (24h accept, 4h pay) appear in **three mandatory places**: the relevant card (CountdownPill), the detail header (banner), and email subject where applicable. Past-deadline UI flips immediately on sweep (poll/Ably) — no stale "3 seconds left" states; client clocks never authoritative (server `expires_at` rendered, drift-corrected).
