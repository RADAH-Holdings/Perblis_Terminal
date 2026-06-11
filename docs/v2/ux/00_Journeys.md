# Terminal v2 — Stage 6 · UX Specification
## 00 · Canonical Journeys
v1.0 DRAFT · June 2026 · Companions: 01_Flows · 02_Hirer_App_Screens · 03_Supplier_Portal_Screens
References: FSD v2 (behaviour) · design-system/ (components by name) · Personas: **Adaeze** (ops lead, 25-asset fleet, 2 yards) · **Emeka** (site manager, Aba) · **Funke** (procurement officer) · **Tunde** (single-excavator owner)

These eight journeys are the acceptance narratives — Stage-6 screens exist to make these paths frictionless, and launch testing (TSD §8) executes them verbatim.

---

### J1 · Supplier onboards a fleet (Adaeze)
Portal. Register → OTP → role intent "Supplier" → **onboarding checklist** appears on dashboard (07 Patterns §4): Business profile → Bank details → First yard → First listing → Verification.
1. Creates **Apapa Equipment Yard** (map pin via LocationIQ search + pin-drop correction), then **PH Laydown & Logistics**.
2. Add asset: 6-step Stepper. Class *Plant & Machinery* → type *Excavator* → spec template renders (doc 05) → pricing (daily ₦75,000, weekly ₦450,000 — PricePreview shows best-price implications) → unit_count 7 → photos (drag-reorder, cover star) → location = yard chip *Apapa* (no map interaction) → review → **Publish blocked**: account not Verified → checklist redirect (07 §7), uploads ID, sees "review within 12h" SLA copy.
3. Next morning: email "You're verified" → publishes; **Duplicate Listing** for the crane (90 seconds); lists PH laydown as *Land & Staging*.
**Outcome:** 25 assets = 2 branded YardPins. Time budget: <60 min excluding verification wait. Failure points designed: geocode wrong (pin-drop correction is primary, search is assist) · verification rejection (reason + resubmit loop).

### J2 · Hirer discovers and pays (Emeka)
App. Install → onboarding (3 screens) → OTP → lands on **Map**.
1. Location permission contextual pre-prompt → granted → map centres Aba; filter chip *Plant & Machinery*; sees BNN YardPin "7" 12.4 km.
2. Tap → **Yard Sheet** (half snap) → CAT 320 row → **Listing Detail**: gallery, SpecTable, AvailabilityStrip, LockedTerms-estimate.
3. **Request flow**: dates 12→26 Jun → duration line "14 days → 2 × weekly — best price ✓" → note ("Site off Aba-Owerri Rd; need operator") → acknowledgment (operator-included) → submit → "Awaiting supplier — 24h" + My Hires badge.
4. Push…no — **email** + in-app: accepted. Hire card shows CountdownPill 4:00:00 → **Pay now** → Paystack sheet (card) → return → polling → **Confirmed** + stamp moment + receipt share card.
**Outcome:** request <10 min from install; zero support contact. Failure paths: payment fail (retry copy with attempts), window expiry (dates released message), 409 race ("dates just taken" + alternatives).

### J3 · Handover to off-hire (Emeka + Adaeze's site rep)
Start date: both get "Handover today" prompts. Either initiates **HandoverCapture**: 4 photos checklist, hour-meter reading, notes → other party confirms (ConfirmPanel ticks) → status **On Hire** (green pulse). End date +: off-hire capture (same anatomy, return reading) → both confirm → **Completed** → Adaeze sees "payout queued"; payout email when founder executes. Skip path: neither documents → auto-complete at end+48h with "no handover record" flag noted in hire detail (dispute-weakening copy shown beforehand).

### J4 · Decline, expiry, and cancellation (the unhappy paths)
- Adaeze declines a too-short request with reason → hirer sees "Declined: {reason}" + similar listings row (soft landing).
- A request sits 24h (Adaeze travelling) → auto-**Expired**; hirer notified with re-request CTA; Adaeze sees "Expired — you missed this request" (accountability copy) on her list.
- Funke cancels a confirmed hire 5 days out → refund preview manifest ("100% refund — ₦612,000") → confirm → refund tracked in hire detail; supplier notified with strike-free copy.
- Adaeze cancels a confirmed hire (breakdown) → penalty-free path requires evidence note; hirer 100% refund + apology copy + similar listings; strike recorded silently against supplier policy ladder.

### J5 · Company evaluation (Funke)
From a crane listing → supplier card → **Storefront**: badge, 2 yards (mini-maps), 25 listings, about. → "Message BNN" general enquiry: "Need 2 excavators + laydown in Apapa, 6 weeks" → one conversation, MaskedContact active → BNN replies referencing listings (listing chips in message? **MVP: plain text + links**) → Funke books two listings; both hires reference the same conversation history.
**Outcome:** company-level trust → multi-line booking. The storefront answers "who am I dealing with" in <30 seconds.

### J6 · Fleet operations (Adaeze, weekly rhythm)
Dashboard Monday: "Action needed 3" (amber stat) → hires table filtered Requested → accept ×2, decline ×1 → **CalendarGantt**: sees PH tippers idle while Apapa saturated → moves two tippers' listing to PH yard (edit → yard chip) → map updates. Messages: 6 unread across 4 conversations — thread rows show listing+yard context. Friday: payout email ₦810,000 → matches dashboard "payout queued" figure.

### J7 · Trust & safety (report → Ops)
Hirer reports a listing ("photos look stock") → confirmation + 24h SLA copy. Ops Console: reports queue shows listing + sibling listings + supplier context → founder removes listing with reason → supplier notified (removed_by_admin state, appeal copy) → reporter thanked. Repeat-bypass case: masked-contact violation reported in chat → warning ladder applied (09 Content §4).

### J8 · The second hire (retention — the metric that matters)
Emeka, 3 weeks later, needs tippers. Opens app → Map remembers last region/filters → his hire history informs "Hire again" row on Hires tab (same listing, new dates, 2 taps to request). Target: ≥30% of completed-hire hirers reach this journey within 60 days (FSD §11). Every design decision that adds friction here is a leakage subsidy.

---

## Journey → Screen coverage matrix
| Journey | Screens exercised |
|---|---|
| J1 | Portal: Auth, Onboarding checklist, Yards, Asset form (all 6 steps), Verification, Dashboard |
| J2 | App: Onboarding, Map, Yard Sheet, Listing Detail, Request flow, Pay, My Hires, Hire Detail |
| J3 | App: Handover capture ×2, Hire Detail timeline; Portal: Hire Detail |
| J4 | Both: Hire Detail states, refund preview, decline/cancel dialogs |
| J5 | App: Storefront, Conversation; Portal: Messages |
| J6 | Portal: Dashboard, Hires table, Calendar, Asset edit, Messages |
| J7 | App: Report sheet; Ops queues |
| J8 | App: Hires tab "Hire again", Map (state restore) |
