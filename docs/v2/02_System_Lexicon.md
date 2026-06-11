# Terminal v2 — Stage 1b: System Lexicon
The canonical vocabulary for every entity, state, and surface in Terminal.
v0.1 DRAFT for founder review · June 2026 · Follows 01_Product_Definition.md (Supplier/Hirer approved)

**Naming principles applied throughout:**
1. **Use the industry's own words** — Nigerian plant-hire runs on British construction English (*hire, plant, yard, on-hire, off-hire, enquiry*). Sound like the market, not like a tech product visiting it.
2. **One concept, one word, everywhere** — UI, API, database, and docs use the same term (UI may use the human form, code the snake_case form, but never a different *word*).
3. **A name must say which side of the market it's on** or be genuinely neutral.
4. **Distinguish the thing from the offer of the thing** — an *Asset* is physical; a *Listing* is its market offer.

---

## 1. Parties & Accounts

| v1 term | v2 term | Code | Rationale |
|---|---|---|---|
| Owner | **Supplier** | `is_supplier`, `SupplierProfile` | Approved (01 §1.2). Procurement language; imports the "Verified Supplier" trust framework. |
| Renter | **Hirer** | `is_hirer` | Approved. The market's own word — *plant hire*. |
| Both | **Dual account** | both flags true | Aligns with Policy Bible §2.2. Not a third identity — a mode switch. |
| Admin / Superuser | **Operator (Terminal Ops)** → surface is the **Ops Console** | `is_staff` | "Admin panel" is generic; "Ops Console" says what it does — runs the platform's operations (KYC queue, disputes, moderation). No collision with *machine operator* because it's an internal-only term, never shown to market users. |
| Guest | **Guest** | — | Fine as-is; universally understood for browse-without-account. |
| Business entity behind a supplier | **Business** (profile section: "Business Profile") | `SupplierProfile.business_*` | Keep plain; "Company" and "Business" are interchangeable — pick **Business** once and stop. |

## 2. Supply Side — Assets & Listings

| v1 term | v2 term | Code | Rationale |
|---|---|---|---|
| (implicit) the physical thing | **Asset** | `asset` (concept) | The umbrella word for anything hireable. Already in the product's DNA ("heavy asset leasing"). |
| Listing | **Listing** *(retained)* | `Listing` | A listing is the *published offer* of an asset: photos, price, location, terms. Precise, neutral, SEO-native ("excavator listing"). Renaming for its own sake would cost clarity. |
| Asset Class (5 categories) | **Asset Class** *(retained)* | `asset_class` (rename field from `resource_type`) | "Resource type" was the weakest v1 word — *resource* is project-management jargon. The classes ARE asset classes; the field should say so. |
| Heavy Equipment class | **Plant & Machinery** | `plant_machinery` | The industry term — Nigeria says *plant hire*, not *heavy equipment rental*. Instantly credible to suppliers; "Heavy Equipment" retained as a search synonym. |
| Vehicles & Transport | **Trucks & Haulage** | `trucks_haulage` | What the market calls it. "Vehicles & Transport" sounds like a ministry. |
| Warehouses & Storage | **Warehousing & Storage** *(near-retained)* | `warehousing` | Industry-standard form. |
| Terminals & Container Yards | **Terminals & Container Yards** *(retained)* | `terminals_yards` | Already the market term; it names the company. |
| Facilities & Staging Areas | **Land & Staging** | `land_staging` | "Facilities" is vague (a warehouse is also a facility). What's actually sold here is *land*: laydown yards, fabrication yards, marshalling areas. |
| Sub-category | **Asset Type** | `asset_type` | "Excavator" is a *type* of asset, not a "sub-category" — speak product, not taxonomy. |
| (fleet spec) Yard / Site | **Yard** *(confirmed)* | `Yard` | Plant-hire native ("equipment yard"). *Depot* rejected (transport-specific); *Site* rejected (in this industry "site" means the **hirer's** project site — a fatal ambiguity we now avoid everywhere: supplier locations are Yards, hirer locations are Sites). |
| (fleet spec) Unit / quantity | **Unit** *(confirmed)* | `unit_count`, `Unit` | An individual machine within a listing ("Tipper #4"). Plain and exact. |
| specifications (JSON) | **Specs** | `specs` | UI says "Specs"; everyone does. |
| Listing verification tiers | **Basic / Verified / Inspected** | `basic`, `verified`, `inspected` | Adopt Policy Bible §3.4 — *Inspected* (third-party physical check) is a far stronger top tier than v1's vague "Premium". |
| Listing statuses | **Draft / Live / Paused / Archived / Removed** | `draft`, `live`, `paused`, `archived`, `removed` | "Active" is freed up for the hire lifecycle (where it caused collision in v1 — an "active listing" and an "active booking" meant unrelated things). A published listing is **Live** — also the word suppliers use ("is it live?"). |
| Inventory (portal nav) | **Assets** | — | Portal nav reads: *Dashboard · Assets · Hires · Calendar · Messages · Storefront · Settings*. "Inventory" is retail/stock language; a supplier manages their **assets**. ("Fleet" rejected — too vehicle-specific for warehouses/land.) |

## 3. Demand Side — The Hire Lifecycle

| v1 term | v2 term | Code | Rationale |
|---|---|---|---|
| Booking | **Hire** | `Hire` model | Approved (01 §1.2). "My Hires", "Active Hires". |
| Booking request | **Hire Request** | status `requested` | — |
| `pending_owner` | **Requested** | `requested` | Status names should be states, not audiences. "Pending owner" leaked an implementation detail into a name. |
| — *(new, from Policy Bible §5.2)* | **Expired** | `expired` | Supplier didn't respond within 24h. v1 had no name for this — and an unnamed state is an unbuilt state. |
| `accepted` | **Accepted** *(retained)* | `accepted` | Awaiting payment (4h window per Policy Bible). |
| `declined` | **Declined** *(retained)* | `declined` | — |
| (paid, in use) `active` | **On Hire** | `on_hire` | The industry's exact term — equipment out with a hirer is "on hire". Unambiguous, and frees "active" entirely. |
| `completed` | **Completed** *(retained)*; the *event* of ending is **Off-Hire** | `completed`; event `off_hire` | "Off-hire" is the industry verb for ending a hire ("we off-hired the crane Friday"). Status stays *Completed*; the return/handover event is the *off-hire*. |
| `cancelled_renter` / `_owner` / `_admin` | **Cancelled** + `cancelled_by` field | `cancelled`, `cancelled_by: hirer\|supplier\|ops` | Three statuses encoding one fact + one attribute was v1 modelling debt. One state, one attribute. |
| `disputed` | **In Dispute** | `in_dispute` | Reads as a state, not an accusation. |
| Pickup / handover | **Handover** (start) | `handover` | Policy Bible's documented-handover flow (photos, meter reading, signature) becomes a named object: the **Handover Record** — one at on-hire, one at off-hire. |
| Return | **Return** *(retained)* | `return` | Plain wins. ("Demobilization" rejected — project jargon, scary in UI.) |
| Extension | **Extension** *(retained)* | `HireExtension` | Policy Bible §5.5. |
| gross_amount | **Hire Value** | `hire_value` | "Gross amount" is accounting-speak; "hire value" is what the market quotes. |
| commission_amount | **Service Fee** (user-facing) / commission internally | `service_fee` | To a supplier, "commission" smells like a broker — the thing Terminal replaces. "Service fee" frames it as payment for a service (storefront, demand, records, payment rails). Finance docs may still say commission. |
| owner_amount | **Supplier Payout** | `payout_amount` | Says exactly what it is and when it matters. |
| Security deposit | **Deposit** *(retained)* | `deposit` | — |
| Date conflict | **Availability conflict** | — | "Date conflict" sounds like a calendar bug; the listing is simply *unavailable*. |

**The lifecycle now reads like English (and like the industry):**
*Requested → Accepted → (paid) → On Hire → Off-Hire → Completed*, with *Expired / Declined / Cancelled / In Dispute* as exits.

## 4. Communication & Trust

| v1 term | v2 term | Code | Rationale |
|---|---|---|---|
| Thread | **Conversation** | `Conversation` | "Thread" is forum-speak; users have conversations. |
| Enquiry thread | **Enquiry** *(retained)* | `enquiry` | British spelling, industry-native — plant-hire firms literally have "Enquiries" desks. |
| Booking thread | **Hire conversation** | `conversation.hire` | Follows the Hire rename. |
| Message | **Message** *(retained)* | `Message` | — |
| Listing report | **Report** *(retained)* | `Report` | "Flag" is the admin's verb; "report" is the user's act. Keep Report as the object. |
| KYC | **Verification** (user-facing); KYC internally | `verification_*` | Nobody outside fintech knows "KYC". UI says "Verify your identity / business". |
| Verification levels | **Basic → Verified → Business Verified** | per Policy Bible §2.3 | Adopt the Policy Bible's 3-level account ladder; maps cleanly to Phase-3 NIN/BVN/CAC. |

## 5. Platform Surfaces

| v1 term | v2 term | Rationale |
|---|---|---|
| Owner Web App | **Supplier Portal** | Approved. |
| Renter Mobile App | **Terminal app** | The consumer-named surface is just *Terminal* — hirers are the default audience of the brand. Internally: "hirer app". |
| Company profile page | **Storefront** | Confirmed from fleet spec — a supplier's public, transacting presence. |
| Django Admin panel | **Ops Console** | See §1. |
| Map home screen | **The Map** | It's the product's front door; it gets a definite article, not a feature name. |
| Map pin types | **Asset Pin / Yard Pin / Cluster** | Confirmed from fleet spec §3. |
| Yard bottom sheet | **Yard Sheet** | Confirmed. |

## 6. Conflicts the Research Docs Introduce (flagged now, resolved in Stage 2/4)

The Policy Bible is hereby adopted as a **planning input of equal rank to the old FSD** — but the two disagree materially, and the Policy Bible is equipment-only while Terminal is five asset classes. To reconcile at MVP-scope stage:

1. **Commission structure** — FSD v1: per-class tiered rates (12/10/8 … 10/8/6) + ₦2,500 *flat fee* under ₦25,000. Policy Bible: single 12/10/8 ladder for all categories + ₦25,000 *minimum hire value* + ₦2,500 *minimum service fee*. These are different business models. (The Policy Bible's minimum-fee formulation is cleaner than the flat-fee override; the per-class differentiation is worth keeping. Recommendation pending Stage 2.)
2. **Duration boundaries** — FSD: weekly = 7–27 days, monthly = 28+. Policy Bible: weekly = 7–29, monthly = 30+. Pick one (and fix the v1 edge case where 8 days = 2 weekly rentals).
3. **Scope** — Policy Bible covers equipment only (its categories even differ: adds Power/Concrete, omits warehouses/terminals/land). Its *policies* (cancellation, deposits, handover) must be generalized or varied per asset class — a warehouse hire has no "hour meter reading".
4. **Payment-before-hire** — Policy Bible assumes real payments (4h window, payout schedules, deposit escrow). Stage 2 must decide what the MVP simulates vs. ships (the v1 "mark as paid" simulation now has much better-defined real behaviour to simulate).
5. **Contact masking / bypass enforcement** (Policy Bible §11.5) — strong anti-leakage posture (masked numbers, keyword detection). Stage 2 must decide how much ships in MVP; it interacts directly with the leakage risk identified as existential.
6. **Launch geography** — Policy Bible: Lagos-only, priority areas Lekki/VI/Ikoyi. Product definition: Apapa–Tin Can industrial axis. Both are Lagos-corridor strategies; sequencing decision for go-to-market, not architecture.

The **architecture decisions doc** (Django + Ninja, Celery+Redis, Pusher, R2, custom User model, service-layer pattern) is logged as the opening position for **Stage 3** — not re-litigated here, but I'll pressure-test Ninja-vs-DRF and Pusher-vs-Ably there with recommendations.

## 7. Sign-off Checklist (Stage 1b)

1. ✅/❌ Asset / Listing / Yard / Unit hierarchy with **Site reserved for the hirer's location**
2. ✅/❌ Asset class renames: **Plant & Machinery**, **Trucks & Haulage**, **Land & Staging** (others retained)
3. ✅/❌ Hire lifecycle: **Requested → Accepted → On Hire → Completed** (+ Expired, Declined, Cancelled+`cancelled_by`, In Dispute), **Live** for published listings
4. ✅/❌ **Service Fee** (user-facing) for commission; **Hire Value / Supplier Payout** for the money fields
5. ✅/❌ **Conversation/Enquiry**, **Verification** (not KYC) user-facing, **Ops Console**, **Terminal app / Supplier Portal / Storefront**
6. ✅/❌ Policy Bible adopted as planning input; the six conflicts above scheduled for Stage 2 resolution
