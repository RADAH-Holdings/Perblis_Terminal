# Terminal — Fleet Owner UX Specification
**Multi-Asset Owners, Yards, and Company Representation**
v1.0 · June 2026 · Companion to FSD v1.0 (extends §9.4, §10, §11, §12)

---

## 1. Problem Statement

The FSD models the marketplace as **one pin = one listing**. This works for Tunde with one excavator. It breaks for the actual supply side of this market, which looks like:

- **BNN Oil & Gas**: 40 assets — excavators, cranes, lowboy trailers — parked in two yards (Apapa, Port Harcourt)
- **A 3PL operator**: one address that is simultaneously a warehouse listing, a container yard listing, and a laydown area listing
- **A truck fleet owner**: 12 identical tippers at one depot

Three distinct failures occur in the current spec:

1. **Map failure (pin stacking).** 40 listings at one coordinate render as 40 overlapping pins — or one pin hiding 39. The renter cannot perceive supply density, and tapping is ambiguous.
2. **Identity failure (no company surface).** The owner exists only as a card inside a listing detail. A fleet company has no storefront — no way for a renter to ask "what else does this company have?", and no way for the company to present credibility (which is the currency of this market).
3. **Inventory failure (identical units).** 12 identical tippers must be 12 near-duplicate listings. The renter sees clutter; the owner manages 12 calendars; date-conflict detection blocks a booking on tipper #1 even though #2–#12 sit idle.

This document specifies the UX solution for all three, the affected user journeys, and the full user-story backlog.

---

## 2. Conceptual Model — Three New Concepts

The fix is a small semantic hierarchy layered on top of the existing Listing model. Crucially, **none of it changes the booking engine** — bookings still attach to a listing.

```
Owner (company)
 └── Yard / Site  (a named location: "BNN Apapa Yard")
      └── Listing (an asset type at that yard: "CAT 320 Excavator")
           └── Unit (an individual physical machine: "CAT 320 #3")  [optional]
```

### 2.1 Yard (Site)
A **Yard** is a named, pinned location an owner attaches listings to. One owner can have many yards; one yard has one coordinate pair and many listings.

- Fields: `id`, `owner`, `name` ("Apapa Equipment Yard"), `location` (PointField), `address_text`, `city`
- A listing belongs to **zero or one** yard. Listings without a yard behave exactly as today (own pin, own coordinates) — full backward compatibility with everything already built server-side.
- When a listing joins a yard, it inherits the yard's coordinates.
- **Why renters care:** the yard is what they actually visit. Distance, access road, security — these are yard properties, not asset properties.

### 2.2 Company Storefront
Every owner already has an `OwnerProfile` (business name, logo, description). The storefront is a **public, renter-facing screen** rendering that profile plus their live inventory. No new data — it is a new *view* on existing data.

### 2.3 Units (quantity) — recommended but severable
A listing gains `unit_count` (default 1) and optionally named units. Conflict detection changes from "any overlap = reject" to "overlapping confirmed bookings ≥ unit_count = reject."

> **Severability note:** Yard and Storefront are pure additive UX + one small model. Units touch the booking conflict logic — if you want zero backend risk right now, ship Yards + Storefront first and let identical machines remain separate listings grouped visually by yard (§5.4 fallback). The UX below is written so Units can land later without rework.

---

## 3. Map Representation — The Pin Hierarchy

The map gets **three pin types**, resolved in this order:

| Pin type | When | Visual | Tap behaviour |
|---|---|---|---|
| **Asset pin** | Single listing, not in a yard | Category icon, category colour | Preview card → Listing Detail |
| **Yard pin** | ≥2 active listings share a yard (or exact coordinates from one owner) | Owner logo (or initials) in a squircle + **count badge** ("12") + small category-dot strip beneath showing which classes are present | Yard Sheet (§3.2) |
| **Cluster pin** | Multiple *different* pins (any type) collide at current zoom | Neutral circle with total count | Zoom in one level, or at max zoom open Cluster Sheet listing the pins inside |

**Key rule — yard pins are semantic, clusters are spatial.** A cluster dissolves as you zoom in. A yard pin **never dissolves**: at maximum zoom, BNN's 12 assets in Apapa are still *one* yard pin, because they genuinely are one place. This is the single most important decision in this document — it makes the map legible at every zoom level and makes density an information signal instead of noise.

### 3.1 Yard pin anatomy
```
   ┌─────────┐
   │ [logo]  ⑫│   ← squircle, owner logo/initials, count badge (active listings)
   └────┬────┘
   ●●●          ← up to 3 category dots (HE amber, Vehicles blue, Warehouse green…)
        ▼
```
- Count badge counts **active listings**, not units (12 tippers as one listing = 1).
- If filters are applied, badge shows *matching* count and dims if zero match ("BNN — 0 matching" pins fade to 40% opacity rather than vanish, preserving the renter's mental map).
- Verified owners get the verification tick on the squircle border — the yard pin doubles as a trust signal.

### 3.2 The Yard Sheet (mobile bottom sheet)
Tapping a yard pin opens a bottom sheet (half-screen, draggable to full):

```
─────────────────────────────
 [logo] BNN Oil & Gas ✓        12 assets · 4.2 km
 Apapa Equipment Yard
 ─ filter chips: All(12) Equipment(7) Vehicles(5) ─
 ┌──────────────────────────┐
 │ ▣ CAT 320 Excavator      │  ₦75,000/day   Available
 │ ▣ 50T Mobile Crane       │  ₦210,000/day  Available
 │ ▣ Tipper Truck ×8 units  │  ₦45,000/day   6 of 8 free
 │ …                        │
 └──────────────────────────┘
 [ View Company Profile → ]
─────────────────────────────
```
- Rows grouped by asset class, sorted by availability then price.
- Distance shown **once** (yard-level) — not repeated per row; they are all the same place.
- Tapping a row → standard Listing Detail (unchanged from FSD §11.4).
- Footer link → Company Storefront.

### 3.3 Search results list view
The list view (FSD §11.2 "Search Results") gains a **group-by toggle**: `By Asset | By Location`.
- **By Asset** (default, unchanged): flat list of listings, but rows belonging to a yard show a small "📍 BNN Apapa Yard · +11 more here" sub-line, tappable to the Yard Sheet.
- **By Location**: results collapse into yard cards (logo, name, distance, matching asset count, price-from) with solo listings interleaved. This is the "I want one supplier for my whole project" mode.

---

## 4. Company Storefront

**Route (mobile):** pushed screen from Yard Sheet footer, owner card on Listing Detail, or sender avatar in chat.
**Route (web, post-MVP SEO surface):** `/company/:slug`.

Layout, top to bottom:
1. **Header** — logo, business name, verification badge, member-since, city/cities of operation
2. **Stats strip** — total active listings, asset classes covered, (post-MVP: response time, rating, completed bookings)
3. **About** — `business_description`
4. **Locations** — horizontally scrollable yard cards, each with a mini-map thumbnail and asset count; tapping recentres the main map on that yard
5. **Inventory** — all active listings, filter chips by class, standard listing cards
6. **CTA** — "Message BNN Oil & Gas" → general enquiry (§6.2)

**What the storefront deliberately is NOT:** it has no booking button of its own. Booking always flows through a listing — keeping the engine untouched and pricing unambiguous.

---

## 5. Multi-Unit Listings

### 5.1 Owner side
In Create Listing Step 1, after sub-category: *"How many identical units of this asset do you have at this location?"* — stepper, default 1. Optional per-unit labels/serials (plate numbers for trucks).

### 5.2 Renter side
- Listing card/detail shows "**8 units** · 6 available your dates" once dates are chosen.
- Booking flow is unchanged for the renter — they book *the listing*; the system assigns a free unit. (Unit assignment is an owner-side concern; renters rent capacity, not serial numbers.)

### 5.3 Availability semantics
- Listing is "fully booked" for a range only when overlapping confirmed/active bookings = `unit_count`.
- Calendar (owner web) shows the listing as a **lane per unit** or a stacked utilisation bar ("6/8 booked").

### 5.4 Fallback if Units are deferred
Owner duplicates the listing per machine ("Tipper #1…#8"); all join the same yard. The Yard Sheet groups identical titles into one visual row with "×8" and expands on tap. Renter experience approximates §5.2 with zero backend change. (The web app should ship a **"Duplicate Listing"** action either way — it's the highest-leverage fleet onboarding feature regardless.)

---

## 6. Messaging Adjustments

### 6.1 Thread context
Threads remain listing-bound (per data model §13.5). But a fleet owner receiving 30 enquiries needs context fast: thread list rows on both apps show **listing thumbnail + listing title + yard name**.

### 6.2 General (company-level) enquiry
The storefront "Message" CTA creates an **enquiry thread with `listing = null`** — "I need 2 excavators and a laydown yard in Apapa for 6 weeks, what can you do?" is the single most natural fleet-market message and the current model cannot carry it.
> ⚠️ **Backend touch:** `Thread.listing` must become nullable for this. If the server is frozen, defer: CTA instead opens a listing picker ("Which asset is this about?") — workable, but measurably worse for the cross-asset project enquiry that fleet customers actually send.

---

## 7. Owner Web App Adjustments (Fleet Scale)

| Screen | Change |
|---|---|
| **/inventory** | Add Yard column + yard filter; group-by-yard view toggle; bulk action "Assign to yard"; **Duplicate Listing** action (pre-fills everything, clears photos optional) |
| **/inventory/new** | Step 5 (Location) becomes: *"Pick a saved yard or drop a new pin"* — saved yards as one-tap chips. Cuts fleet listing time massively |
| **/yards** (new, simple) | CRUD for yards: name, pin, address. A yard with listings cannot be deleted, only renamed/moved |
| **/bookings/calendar** | Y-axis groups listings under yard headers; multi-unit listings render utilisation ("6/8") or expandable unit lanes |
| **/dashboard** | Stats segment by yard when owner has >1 yard ("Apapa: 3 pending · PH: 1 pending") |

---

## 8. User Stories (Backlog)

### EPIC A — Yard & Map Discovery

**A1.** As a *fleet owner*, I want to create a named yard with one map pin so that I don't drop 40 individual pins for assets parked in the same place.
*AC:* Yard has name + pin + address; listings can be attached at creation or from inventory bulk action; listing inherits yard coordinates.

**A2.** As a *renter*, I want co-located listings from one owner to appear as a single yard pin with a count, so the map stays readable and I can see supply density at a glance.
*AC:* ≥2 active listings sharing a yard render one yard pin; badge = active listing count; pin persists at all zoom levels.

**A3.** As a *renter*, I want to tap a yard pin and see everything available there grouped by category, so I can evaluate a supplier's whole offer without leaving the map.
*AC:* Bottom sheet ≤500ms; class filter chips; rows show price-from and availability; row → Listing Detail; footer → storefront.

**A4.** As a *renter filtering the map* (e.g., "Warehouses only"), I want yard pins to show how many *matching* assets they contain, so filters stay meaningful at yards.
*AC:* Badge updates to match count; zero-match yards dim to 40% opacity, not removed.

**A5.** As a *renter*, I want spatial clusters (different owners, low zoom) to behave differently from yards, so I'm never confused about whether pins are "one place" or "zoomed-out many places."
*AC:* Cluster pin tap = zoom-in; at max zoom, cluster sheet lists contained pins; visual style clearly distinct (neutral circle vs branded squircle).

**A6.** As a *renter using list view*, I want to toggle between "by asset" and "by location" grouping, so I can either compare machines or pick one supplier for a whole project.

**A7.** As a *solo owner* (one excavator, no yard), I want my listing to work exactly as before, so the yard system costs me nothing.
*AC:* Yard is optional everywhere; solo listing = classic asset pin.

### EPIC B — Company Storefront

**B1.** As a *fleet owner*, I want a public company profile showing my logo, verification, yards, and full inventory, so my credibility converts into bookings.

**B2.** As a *renter*, I want to open the company profile from any listing, yard sheet, or chat avatar, so I can answer "who am I dealing with and what else do they have?"

**B3.** As a *renter*, I want each yard on the profile to show a mini-map and asset count, and tapping it to recentre the main map there, so the profile and the map stay connected.

**B4.** As a *renter*, I want to message a company directly from its profile about a multi-asset need, so I don't have to fabricate a per-listing enquiry. *(Depends on nullable Thread.listing — see §6.2 for fallback.)*

**B5.** As the *admin*, I want to view a company's storefront as renters see it, so listing-report reviews include the supplier context.

### EPIC C — Multi-Unit Inventory

**C1.** As a *fleet owner with 8 identical tippers*, I want one listing with a unit count instead of 8 duplicates, so my inventory and the renter's results stay clean.

**C2.** As a *renter*, I want to see "6 of 8 available for your dates," so identical-unit supply reads as one strong option, not eight confusing ones.

**C3.** As a *fleet owner*, I want overlapping bookings accepted until all units are committed, so I stop losing bookings to false conflicts.
*AC:* Conflict check compares overlap count to unit_count; acceptance assigns a unit; unit labels visible to owner only.

**C4.** As a *fleet owner*, I want the calendar to show per-listing utilisation (6/8) with expandable unit lanes, so I can see true fleet capacity.

**C5.** As a *fleet owner*, I want to "Duplicate Listing" with everything pre-filled, so listing machine #2 takes 60 seconds, not 10 minutes. *(Ship this even if Units land — it covers near-identical assets too.)*

### EPIC D — Fleet Onboarding & Management (Owner Web)

**D1.** As a *fleet owner onboarding*, I want to create my yards first and then attach listings to them via one-tap chips in the location step, so listing 40 assets doesn't mean 40 map interactions.

**D2.** As a *fleet owner*, I want inventory filterable and groupable by yard, with bulk pause/archive/assign-to-yard, so I can manage by location the way my operations actually run.

**D3.** As a *fleet owner*, I want dashboard attention items segmented by yard, so my Apapa manager and PH manager can each see their queue. *(Single-login MVP; per-yard staff accounts are a Phase 6 note.)*

**D4.** As a *fleet owner*, I want thread list rows to show which listing and yard each conversation concerns, so 30 simultaneous enquiries stay navigable.

### EPIC E — Trust & Edge Cases

**E1.** As a *renter*, I want the yard pin to carry the owner's verification badge, so density and trust read in one glance.

**E2.** As a *renter*, when two **different owners** genuinely share a coordinate (shared industrial estate), I want them as separate pins (spider-fanned at max zoom), never merged into one yard — a yard is one owner by definition.

**E3.** As the *admin*, I want listing reports to surface sibling listings from the same owner/yard, so one fraudulent listing prompts review of the whole storefront.

**E4.** As a *renter on poor connectivity*, I want yard sheets to load from already-fetched map payload data (listing summaries ride along with pins), so the sheet opens instantly offline-ish.

---

## 9. Revised User Journeys

### Journey 5 — Fleet Owner Onboards (extends FSD Journey 1)
*Adaeze is operations lead at BNN Oil & Gas: 7 excavators, 5 cranes, 8 tippers in Apapa; a laydown yard and 4 trucks in Port Harcourt.*

1. Registers on the web app, selects Owner, completes business profile (logo, CAC name, bank).
2. Prompted: *"Where are your assets located? Create your first yard."* Creates **Apapa Equipment Yard** (pin + address), then **PH Laydown & Logistics**.
3. Creates "CAT 320 Excavator" listing → Step 5 shows yard chips → taps *Apapa* — no map interaction needed. Sets unit count = 7 *(or duplicates ×7 under the fallback)*.
4. Duplicate-and-edit for the crane listing (10 min total for the heavy equipment).
5. Lists the PH laydown yard as a Facilities listing pinned to the PH yard.
6. Map check: Terminal now shows **two BNN-branded pins in all of Nigeria** — one badge "20" in Apapa, one badge "5" in PH. Not twenty-five scattered pins.

*Result: a 25-asset fleet onboarded in under an hour, rendered as two legible, branded supply points.*

### Journey 6 — Renter Books from a Fleet (extends FSD Journey 2)
*Emeka needs an excavator AND a tipper for the same site, 2 weeks.*

1. Map, filtered "Equipment" — sees the BNN yard pin: logo, badge "7 matching", 12.4 km, verified tick.
2. Taps pin → Yard Sheet: excavators and cranes grouped, prices from ₦75,000/day.
3. Books the CAT 320 (standard flow, unchanged). Duration preview, price breakdown, submit.
4. Back on the Yard Sheet (preserved state), clears filter, sees "Tipper Truck — 6 of 8 available", books it too.
5. Both bookings land with the same owner; his Messages show two threads, each labelled with listing + "BNN Apapa Yard."

*Result: a two-asset, one-supplier project assembled in one map session — the exact transaction shape the offline market does by phone today.*

### Journey 7 — Renter Evaluates a Company Before Committing
*Funke (procurement, construction firm) is risk-averse and supplier-oriented.*

1. From a crane listing, taps the owner card → **BNN storefront**.
2. Sees: verified badge, 25 active listings across 2 yards, professional description, member since.
3. Uses "Message BNN" with a project brief covering three asset types; gets one coherent reply.
4. Books two of the three through their listings; sources the third elsewhere on the same map.

*Result: company-level trust converts into multi-line bookings — the storefront is the B2B sales surface.*

### Journey 8 — Fleet Owner Runs a Multi-Yard Operation (extends FSD Journey 3)
1. Adaeze's dashboard: "Apapa: 3 pending requests · PH: 1 pending."
2. Calendar grouped by yard; tipper listing shows 6/8 utilisation bar — she sees PH trucks idle while Apapa is saturated.
3. (Insight, manual in MVP): she relocates two tippers to PH and edits the listing's yard assignment — the map updates instantly.

*Result: Terminal becomes her fleet utilisation dashboard, which is retention the chat-leakage problem can't touch.*

---

## 10. Implementation Notes & Sequencing

**Backend deltas (kept deliberately minimal):**
| Change | Size | Required for |
|---|---|---|
| `Yard` model + `Listing.yard` nullable FK | Small, additive | Epics A, B, D |
| Map endpoint: aggregate listings sharing a yard into one feature with `listing_summaries[]` | Medium (search app only) | A2–A4, E4 |
| Public owner profile endpoint (`/api/companies/:id`) | Small, read-only composition of existing data | Epic B |
| `Listing.unit_count` + conflict-check change | Medium, touches booking engine | Epic C (severable) |
| `Thread.listing` nullable | Small but schema-touching | B4 only (has UI fallback) |

**Suggested build order (fits the wave-gating workflow):**
1. **Wave F1 — Yards + pin hierarchy + Yard Sheet** (kills the pin-stacking failure; biggest visible win)
2. **Wave F2 — Company Storefront** (read-only screen; high trust ROI, near-zero risk)
3. **Wave F3 — Owner web fleet tooling** (yard CRUD, duplicate listing, grouped inventory/calendar)
4. **Wave F4 — Multi-unit listings** (the only wave touching booking logic — last, behind tests)

**Design-system notes:** yard pin = squircle avatar + badge (reuse avatar + badge tokens); category dots reuse the five class colours; Yard Sheet is the same bottom-sheet primitive as the pin preview card, taller snap point.

---

## 11. Open Decisions (need founder sign-off)

1. **Units now or fallback?** §5.4 fallback ships fleets without touching the booking engine; real Units are better but riskier. *(Recommendation: fallback in F1, real Units in F4.)*
2. **Nullable Thread.listing** for company-level enquiry — accept the schema change, or use the listing-picker fallback?
3. **Auto-yard inference:** when an owner creates a second listing within ~100m of an existing one, prompt "Add to Apapa Yard?" — recommended yes (keeps yards accurate without owner discipline).
4. **Storefront URL/SEO** is a Phase-5+ growth lever (public company pages indexable by Google) — flagging now so slugs are reserved early.

— End —
