# Terminal v2 — Stage 2: MVP Scope
v0.1 DRAFT for founder review · June 2026
Inputs: 01_Product_Definition, 02_System_Lexicon, DECISIONS.md (D-001…D-008), Policy Bible, FSD v1 (legacy)

---

## 1. MVP Philosophy

v1's principle was *prove the core loop*. v1 proved it — a simulated loop works. **v2's MVP must prove the thing v1 couldn't: that transactions happen *through* Terminal, with real money, and stay there.**

**The v2 core loop:**
> Supplier lists assets at a Yard → Hirer discovers them on the Map → Hire requested → Supplier accepts → **Hirer pays through Terminal** → On Hire → Off-Hire → both parties hold a complete transaction record.

Two additions vs v1, both deliberate:
- **Money is in the loop** (D-006, collect-only). A marketplace MVP without payment proves discovery, not a business.
- **Fleets are native, not retrofitted.** Supplier → Yard → Listing → Unit is modeled from day one — greenfield makes this nearly free; retrofitting it cost v1 an entire redesign cycle.

Everything that blocks or delays this loop is simulated, manual-behind-the-scenes, or deferred.

## 2. Decisions This Scope Implements

| ID | Decision |
|---|---|
| D-002 | Service fee = per-class rates, `max(rate × hire_value, ₦2,500)` floor |
| D-004 | No minimum hire value |
| D-006 | **Payments: collect-only via Paystack.** Real checkout; fee retained; supplier payouts manual via Ops Console payout queue (weekly). Deposits deferred. |
| D-007 | **Launch: both Lagos corridors**, with class-specific anchors — Lekki–Ajah/Mainland anchored by Plant & Machinery + Trucks & Haulage; Apapa–Tin Can anchored by Terminals, Warehousing, Land. Supply onboarding targets are set *per corridor* (see §8). |
| D-008 | **Duration pricing: best-price rule.** `hire_value = min(daily×d, weekly×ceil(d/7), monthly×ceil(d/30))` over the rates the supplier has set; the winning scheme sets the service-fee tier. |

## 3. In Scope

| # | Module | Contents |
|---|---|---|
| 1 | **Accounts & Verification** | Register (email+phone+password), login, JWT, password reset. Roles: `is_supplier` / `is_hirer` (dual = both). **Real SMS OTP via Termii** (see §5 rationale). Identity document upload → **manual review in Ops Console** (real verification, human process — not auto-approve). Account levels: Basic → Verified → Business Verified. |
| 2 | **Supplier & Storefront** | SupplierProfile (business info, logo, bank details encrypted). **Yards**: named locations with pins; listings attach to yards. **Public Storefront**: header, verification badge, yards, live inventory, enquiry CTA. |
| 3 | **Listings** | All 5 asset classes, one polymorphic Listing model + `asset_type` + `specs` JSON. **`unit_count` native** (identical units under one listing). Photos 1–10 via R2. Pricing: daily required, weekly/monthly optional. Status: Draft/Live/Paused/Archived/Removed. Listing tiers: Basic (auto) — Verified/Inspected machinery exists in model, awarded manually via Ops Console. Reports by hirers. |
| 4 | **Map & Discovery** | Full-screen map home (hirer app). Pin hierarchy: **Asset Pin / Yard Pin / Cluster** per Fleet UX Spec. Yard Sheet. PostGIS radius + viewport search, distance annotation, class filter, text search, price filter. Guest browsing. |
| 5 | **Hires** | Request (dates + note + best-price preview — hirer sees total payable only; fee/payout breakdown renders on supplier surfaces only, D-014). Availability conflict check (unit-aware: overlaps < unit_count ⇒ available). Lifecycle: Requested → Accepted → *paid* → On Hire → Completed; Expired (24h supplier non-response, automated), Declined (reason), Cancelled (+`cancelled_by`), In Dispute (flag + Ops freeze only — no mediation tooling). Extensions deferred. |
| 6 | **Payments (collect-only)** | Paystack checkout on acceptance; **4-hour payment window** (Policy Bible §5.2), expiry auto-cancels and releases dates. Webhook + Celery retry → hire moves to On Hire automatically. Refunds via Paystack API per the MVP cancellation rules (§6). **Payout queue in Ops Console**: list of completed hires with payout amount + supplier bank details; founder marks paid weekly. |
| 7 | **Handover Records (lite)** | At on-hire and off-hire, both parties confirm in-app: ≥2 photos + class-specific reading (see §7) + confirmation tap. Stored against the hire. No digital-signature ceremony, no enforcement deadlines in MVP — the record's existence is the dispute evidence. |
| 8 | **Messaging** | Conversations: Enquiry (listing or storefront level) + Hire conversations. Real-time via managed websockets (Stage 3 decides Pusher vs alternative). Unread badges. **Contact masking until hire is paid** (§6): regex redaction of phone/email patterns in messages pre-payment + warning copy. No keyword surveillance beyond this. |
| 9 | **Ops Console** | Dashboard: GMV, service fees collected, payout liabilities, hires by status, new users. Verification queue (ID review). Payout queue. Listings management + reports queue. Hires oversight + admin cancel. User suspension. |

## 4. Out of Scope (Deferred)

| Feature | Phase | Note |
|---|---|---|
| Automated payouts (Paystack Transfer/split) | 2 | Payout queue is the manual stand-in; same data model |
| Security deposits (card holds / escrow tiers) | 2 | Policy Bible §7 adopted then; MVP listings may state deposit terms as free text |
| Big-ticket fee taper | 2 | D-003 |
| Hire extensions & modifications | 2 | Cancel-and-rebook in MVP |
| NIN/BVN/CAC API verification | 3 | MVP verification is real but manual |
| Reviews & ratings | 4 | Needs completed-hire volume |
| Dispute mediation tooling | 4 | MVP: In Dispute flag freezes payout; founder mediates by hand |
| Push notifications | 3 | In-app badges + transactional email |
| Owner analytics, heatmaps | 5 | — |
| Featured listings, subscriptions, rate-config UI | 6 | — |
| Cross-state hires, expansion | 7 | Lagos only (D-007) |

## 5. Real vs Manual vs Simulated — the v2 strategy

v1 simulated everything risky. v2's rule: **simulate integrations, never simulate trust.** Where v1 faked a process, v2 does it *for real but manually* when a human (founder) can be the engine.

| Capability | v1 | v2 MVP | Why |
|---|---|---|---|
| Payment | Simulated (button) | **Real** (Paystack collect) | The product is the transaction record; a fake transaction records nothing |
| Payouts | — | **Real, manual** (Ops queue) | 30 min/week at MVP volume; identical data model to Phase-2 automation |
| SMS OTP | Simulated (auto-pass) | **Real** (Termii, ~₦4/msg) | With real money, account quality stops being optional; trivial integration |
| ID verification | Simulated (auto-approve) | **Real, manual** (Ops review) | Human review at MVP volume; the queue UI is needed for Phase 3 anyway |
| Deposits | Simulated (field=0) | **Deferred entirely** | Half-real deposits are worse than none; listings state terms as text |
| Push notifications | Badge only | Badge + **transactional email** (Resend) | Email is one integration and covers the "hirer paid / supplier accepted" moments |
| Listing Verified/Inspected tiers | Auto-"Basic" | Basic auto; upper tiers **manually awarded** | Inspection partnerships are post-MVP; the model carries the field now |

## 6. MVP Cancellation & Refund Rules (simplified from Policy Bible §8)

Full matrices arrive with deposits in Phase 2. MVP rules — simple enough to print on one screen:

- **Before payment:** anyone cancels, nothing owed (Requested/Accepted states).
- **Hirer cancels after payment, >72h before start:** 100% refund (Paystack refund; service fee returned).
- **Hirer cancels ≤72h before start:** refund minus one day's hire value (supplier compensation), minus non-refundable processing ~1.5%.
- **Supplier cancels after payment (any time):** hirer refunded 100% including processing cost (Terminal absorbs); strike against supplier (3 strikes = suspension review). No cash penalties in MVP.
- **No-shows:** treated as the corresponding party's cancellation; Handover Record absence is the evidence.

## 7. Per-Asset-Class Policy Variants (resolves Task #1b)

The Policy Bible generalizes across the five classes as follows:

| Policy area | Plant & Machinery | Trucks & Haulage | Warehousing / Terminals / Land |
|---|---|---|---|
| Handover reading | Hour meter | Odometer | None — photos + condition/occupancy notes |
| Handover photos | 4 angles | 4 angles + plates | Entrance, interior/area, access points |
| Condition field | Excellent/Good/Fair | Same | Condition notes free text |
| Operator/driver | Operator-inclusive flag + acknowledgment (PB §12.2) | Driver-inclusive flag + acknowledgment | N/A |
| Late return | Grace 4h, then 1.5× daily rate/day | Same | Occupancy holdover: 1.5× daily equivalent, flagged to Ops at +3 days |
| Mandatory listing fields | Make/model/year/condition | Make/model/year/reg/condition | Area (sqm), access, power/security features |

## 8. Success Criteria

**Business (the ones v1 couldn't measure):**
- ≥ 25 paid hires within 60 days of launch
- ≥ ₦500,000 in service fees actually collected
- ≥ 30% of hirers with a completed hire make a second hire within 60 days (on-platform retention — the leakage metric)
- ≥ 40 live listings at launch: ≥ 25 in the construction corridor (Plant/Trucks), ≥ 15 in the port corridor (Terminals/Warehousing/Land), ≥ 8 supplier storefronts with 3+ listings

**Product:**
- Supplier: register → verified → first Live listing in < 1 day (verification SLA: founder reviews within 12h)
- Hirer: install → discover → request in < 10 minutes; pay in < 4h window without support intervention
- Both parties can complete the full loop including handover records without founder hand-holding

**Technical:**
- Map search < 500ms P95; payment webhook → On Hire transition < 60s; message delivery < 300ms P95
- Zero payment-state inconsistencies (every Paystack event reconciled; daily reconciliation job)
- Refunds processed within 5 business days end-to-end

## 9. Sign-off

1. ✅/❌ Module list (§3) — incl. real OTP, manual verification, handover-lite, contact masking
2. ✅/❌ Real/manual/simulated strategy (§5) — "simulate integrations, never simulate trust"
3. ✅/❌ MVP cancellation rules (§6)
4. ✅/❌ Per-class policy variants (§7)
5. ✅/❌ Success criteria (§8)
