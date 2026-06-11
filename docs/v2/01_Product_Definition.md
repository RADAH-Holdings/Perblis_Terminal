# Terminal v2 — Stage 1: Product Definition & Naming
v0.1 DRAFT for founder review · June 2026
Status: ⏳ Awaiting sign-off before Stage 2 (MVP Scope)

---

## 1. Entity Naming Decision

### 1.1 Why "Owner / Renter" fails the product

- **It's consumer vocabulary.** "Owner/Renter" is Airbnb language — it frames Terminal as a peer-to-peer sharing app. Terminal's counterparties are *businesses*: fleet operators, terminal operators, 3PLs, construction firms, procurement departments. The words on the screen should sound like the words in their contracts and purchase orders.
- **"Owner" describes a legal fact, not a market role.** A company may lease-to-own its excavators (doesn't "own" them), or manage assets it doesn't hold title to. What matters to Terminal is that they *supply* capacity.
- **"Renter" undersells the demand side.** A site manager committing ₦900,000 for two weeks is not a "renter" in the way the word reads in Nigerian English (a residential tenant). He's *hiring plant* — which is, verbatim, what this industry calls it.

### 1.2 The recommendation: **Supplier** and **Hirer**

| v1 term | v2 term | Plural / adjective use |
|---|---|---|
| Owner | **Supplier** | "Supplier Portal", "Verified Supplier", `is_supplier` |
| Renter | **Hirer** | "Hirer app", `is_hirer` |
| Both | (no label — both flags true) | UI: "mode switch", not a third identity |
| Booking | **Hire** (product language) / `booking` acceptable internally | "Request to Hire", "My Hires", "Active Hires" |

**Why Supplier:**
1. It's procurement language. Every B2B buyer in this market has a "supplier list", does "supplier verification", signs "supplier agreements". When Terminal says *Verified Supplier*, a procurement officer instantly knows what that means and what it's worth — the term imports an entire trust framework for free.
2. It's aspirational for the supply side in the right way: Terminal's pitch to a fleet company is "become a discoverable supplier to the whole market", not "list your stuff".
3. It scales across all five asset classes. "Owner" strains for a terminal operator selling container-slot capacity; "Supplier" doesn't.

**Why Hirer:**
1. **It's the market's own word.** Nigeria uses British construction English: the industry is literally called *plant hire*; equipment is "for hire"; the customer is the *hirer*. UK/Commonwealth hire-industry contracts (CPA conditions) use Supplier/Hirer as the standard pair. Terminal adopting the incumbent vocabulary lowers adoption friction — we sound like the industry, not like a tech product visiting it.
2. It's active and time-bound — hiring is an engagement with a start and end, which is exactly Terminal's transaction shape (vs. "lessee", which is correct but legalistic, and confusable with "lessor" at a glance — a genuine UX hazard one letter apart).
3. It unlocks coherent product language end-to-end: *Request to Hire → Hire confirmed → Active Hire → Hire completed*. The status lifecycle reads like English.

**Rejected alternatives, for the record:**
- *Lessor/Lessee* — legally precise, but cold, and dangerously similar typographically. Error-prone in UI, code, and conversation.
- *Partner/Client* — warm but vague; neither says which side of the market you're on, which is the one thing a marketplace label must do.
- *Operator* (supply side) — tempting because "fleet operator" and "terminal operator" are real titles, but it collides fatally with the *machine operator* ("operator-inclusive pricing" is already a spec concept). Killed.
- *Vendor* — reads as selling goods, not supplying capacity. Terminal is NOT a sales platform.

**Naming ripple (to standardize in FSD/TSD):**
- Supplier-side web app: **Supplier Portal** (not "Owner Web App")
- `OwnerProfile` → `SupplierProfile`; roles as booleans `is_supplier` / `is_hirer`
- Public company page: **Supplier Storefront**
- The five categories remain **Asset Classes**; an individual record remains a **Listing** (precise, neutral, SEO-friendly); a supplier location remains a **Yard**

---

## 2. What Terminal Is

**One-line definition:**
> Terminal is the digital infrastructure for hiring heavy assets in Africa — a map-first B2B marketplace where verified suppliers list equipment, vehicles, warehouses, terminals, and industrial facilities, and hirers discover, compare, and book them with structured, recorded transactions.

**Category:** B2B marketplace — but the long-game framing is *asset-utilization infrastructure*. Terminal's product is not the listing; it is **the transaction record** — discoverable supply, verified counterparties, locked commercial terms, and a paper trail, in a market that currently runs on phone calls and trust-by-acquaintance.

**The market reality v2 is built on (learned, not assumed):**
1. **Supply is fleets, not individuals.** The unit of supply is a company with a yard (or several), not a man with an excavator. v2 models Supplier → Yard → Listing → Unit natively from day one.
2. **Trust is the product.** Hirers commit ₦100k–₦1M+ to counterparties they've never met. Every v2 feature is judged by whether it manufactures trust: verification, storefronts, transaction records, locked pricing.
3. **Leakage is the existential risk.** Chat introduces the parties; nothing stops deal #2 happening offline. v2's answer is not to block contact (impossible) but to make staying on-platform *worth more*: payment protection, invoices, booking records, reputation that compounds, and a storefront that markets the supplier for free.
4. **Liquidity is corridor-shaped.** A map of Nigeria with 10 pins is a dead product. Launch is one corridor (Lagos: Apapa–Tin Can–Lekki industrial axis) saturated before any expansion.

## 3. What Makes Terminal Unique

1. **Map-first discovery with real distance.** Supply in this market is location-critical (mobilization cost of moving a 22-tonne excavator dwarfs daily rate differences). PostGIS-computed distance from the hirer's site is decision-grade information no competitor surfaces. The map is the home screen, not a feature.
2. **The Supplier Storefront.** Every supplier gets a branded, verified, inventory-live company page — yards on a map, full fleet, credentials. For a market where reputation travels by word of mouth, this is the first time a Nigerian plant-hire company gets a digital presence that *transacts*. (It is also the anti-leakage asset: the storefront generates the supplier's future demand, and it only exists on Terminal.)
3. **Structured hire lifecycle with locked commercial terms.** Request → accept → active → completed, with gross/commission/net frozen at acceptance and every message timestamped against the hire. The offline alternative is a phone agreement nobody can prove. Terminal's paper trail is the product feature that survives even when payment is offline.
4. **Five asset classes, one platform.** Competitors are single-vertical (freight, classifieds, fleet owners renting their own gear). Real projects need an excavator *and* tippers *and* a laydown yard — Terminal is the only place that's one search. Cross-class supply from a single supplier (the BNN case) is the killer transaction shape.
5. **Built for the trust-poor, infrastructure-poor context.** Verification tiers mapped to Nigerian reality (NIN/BVN/CAC), Paystack rails, NDPR compliance, offline-tolerant mobile UX. Global rental SaaS cannot cheaply localize this; local classifieds cannot cheaply build the transaction layer. That gap is the moat.

## 4. What Terminal Is Not (unchanged, re-affirmed)
- NOT an asset owner — facilitates, never operates
- NOT a logistics company — no transport/delivery arrangement
- NOT a bank — commission collection is the extent of financial activity (payments processing via licensed PSP from Phase 2)
- NOT a sales platform — hire/lease only, never purchase

## 5. Who It Serves

**Suppliers (web-first):** plant-hire companies, fleet operators, terminal/depot operators, warehouse landlords, 3PLs, oil & gas asset holders with idle capacity. Persona anchor: *Adaeze, ops lead at a 25-asset fleet company with yards in Apapa and PH.*

**Hirers (mobile-first):** construction site managers, project procurement officers, importers/freight forwarders needing storage or container handling, manufacturers needing overflow capacity. Persona anchor: *Emeka, site manager in Aba who needs an excavator and two tippers for six weeks, near his site, from someone he can trust.*

**Both-sided:** contractors who own some assets and hire others — both flags on one account, mode switch in UI.

---

## 6. Open Items for Founder Sign-off
1. ✅/❌ **Supplier / Hirer** as the canonical pair (everything downstream inherits this)
2. ✅/❌ "Hire" as the product word for a booking ("Request to Hire", "My Hires") with `booking` retained as the internal/technical term
3. ✅/❌ The one-line definition and the five uniqueness pillars as the product's north star
4. ✅/❌ Corridor-first launch posture (Lagos industrial axis) as a stated product principle, not just a go-to-market detail
