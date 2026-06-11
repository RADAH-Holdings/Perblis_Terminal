# Wave 3 — Discovery: Map Search & Yard Aggregation

**Status:** ⏸ Gated on Wave 2 sign-off
**Depends on:** Wave 2 (Live listings, yards, spec templates with ★ fields)
**Spec references:** FSD §6 (discovery — incl. Acceptance checks, pin hierarchy semantics) · TSD §3.1 (`search`), §3.7 (search & map aggregation — response shape is normative), §3.8 (throttles) · DECISIONS D-013 (MapLibre/OpenFreeMap/LocationIQ) · Fleet UX heritage: yard pins are semantic, clusters are spatial

## Objective

The two read endpoints that power the hirer app's home screen: `search/map` returning **server-aggregated yards** plus solo listings for a viewport/radius, and `search/list` returning the same result set in list form. All grouping, counting, distance, and filtering is server-authoritative — clients only style and spatially cluster what they're given.

## In scope

### 3.1 `GET /api/v1/search/map` (TSD §3.7 — response shape normative)
- Params: `bbox` **or** (`lat,lng,radius_km` ∈ {5,10,25,50,100,custom}) · `asset_class` · `q` (title+description) · `price_min/max` (daily price, kobo) · `spec_min/max` (the ★ field for the active class).
- Response: `yards[]` (yard_id, name, point, supplier{id,name,logo,badge}, **listing_count**, **matching_count**, class_mix, price_from, embedded listing summaries so the Yard Sheet opens with zero extra round-trips) + `listings[]` (solo pins only: id, title, class, point, price_from, distance_km, photo, badge).
- **Aggregation is server-side** GROUP BY yard over Live listings (FSD §6 acceptance: counts authoritative). A yard with ≥2 Live listings emits a yard entry; a yardless or single-listing-yard listing emits a solo entry. Zero-match yards under an active filter still appear with `matching_count: 0` (client dims to 40%, never removes).
- Anonymous access allowed (guest browsing, FSD §6); anon throttle 60/min.

### 3.2 `GET /api/v1/search/list`
- Same params + cursor pagination + `group_by=asset|location`. `asset` = flat listings with `more_at_yard` count for "+N more at this yard" sub-lines; `location` = yard cards interleaved with solo listings, ordered by distance.

### 3.3 Geo correctness
- Distance: `ST_Distance(point, ref::geography)/1000`, rounded 0.1 km, computed server-side **only** (never client-estimated). Ordering by distance.
- Viewport: `point && ST_MakeEnvelope(...)` + GIST index; radius via `ST_DWithin` on geography.
- ★ spec filters via JSONB containment/range on the GIN index (TSD §3.3 listings indexes).
- Only `status=live` listings are ever visible; suspended-supplier listings excluded (their hiding was wired in Wave 2 — assert it holds through search).

### 3.4 Geocoding proxy
- `GET /api/v1/geocode?q=` — LocationIQ server-side (key never reaches clients), 24h cache (DB or in-process LRU — **no Redis**, D-010), graceful "not configured" in dev.

### 3.5 Performance pass
- Seed script generating ~500 in-radius listings across yards; `EXPLAIN ANALYZE` the hot queries; **P95 < 500ms** on Railway hardware (FSD §12). N+1-free (django-debug-toolbar locally / assertNumQueries in tests).

## Out of scope (deferred)

- Availability-aware search ("available for my dates" arrives with Wave 4's availability engine; `available` flags in summaries may stub `true` until then — flagged in the schema description) · ranking/completeness weighting (Phase 2) · saved searches (Phase 2) · client-side clustering & pin styling (Wave 8, per doc 08 §4.2).

## Contracts frozen at wave end

`search/map`, `search/list`, `geocode` — the app's home map (Wave 8) and the portal's pickers consume this freeze. The map response shape in TSD §3.7 is the contract; document every field in the OpenAPI schema.

## Mandatory tests (FSD §6 acceptance checks as named tests)

- Same supplier + same coordinates ⇒ **one** yard pin at every zoom level's bbox.
- Two suppliers at one coordinate ⇒ **two** entries, never merged.
- Solo listing ⇒ `listings[]`; second Live listing added to its yard ⇒ both move into a `yards[]` entry (and out of `listings[]`).
- Filtered `matching_count` correct; zero-match yard still present with count 0.
- Pause/archive/suspend ⇒ disappears from results (and yard counts decrement) immediately.
- ★ spec range filter per class (5 classes × boundary cases); price filter on daily price.
- `q` matches title and description, case-insensitive.
- Distance values match PostGIS reference calc to 0.1 km; list ordering stable.
- bbox vs radius parity on identical data; cursor pagination stability under inserts.
- Geocode proxy: key never in response; cache hit on repeat query.

## Exit criterion (founder demo)

> Against production with seeded dual-corridor data: map JSON is demonstrably correct for the four canonical cases — **solo pin**, **yard pin with counts + embedded summaries**, **filtered counts with dimmed zero-match yard**, **zero-result viewport** — and the seeded 500-listing P95 measurement is < 500ms. Reviewed via `/api/docs/` + a scratch HTML map page (throwaway, not a deliverable).

## Wave-end checklist

- [ ] FSD §6 acceptance checks pass as named tests
- [ ] P95 measurement recorded in the PR (number, not vibes)
- [ ] OpenAPI regenerated & committed; map contract frozen
- [ ] Founder approval recorded before Wave 4 begins
