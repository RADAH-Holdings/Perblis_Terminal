# Terminal v2 — Stage 3b: Asset Spec Schemas
Per-class specification templates for listings.
v0.1 DRAFT for founder review · June 2026 · Feeds FSD §Listings (Stage 4)

---

## 1. How Specs Work (functional model)

- Every listing stores a `specs` JSON object validated against a **Spec Template** — selected by the listing's `asset_class` + `asset_type`.
- A template = **class-common fields** (every type in the class) + **type-specific fields** (only for that asset type).
- Templates are **server-side configuration** (registry, versioned), not hardcoded forms: the portal's listing form and the app's Specs section render dynamically from the template. Adding a field or asset type is config, not a release.
- **Field kinds:** `number` (with unit), `text`, `select` (fixed options), `boolean`, `multi-select`.
- **Required** fields gate publishing (Draft → Live). Optional fields raise a listing's *completeness score* (used for search ranking later; just stored in MVP).
- **Filterable** marks fields that become search filters. MVP keeps filtering to class + price + distance + *one headline spec per class* (marked ★); everything else displays but doesn't filter until Phase 5.
- Every class includes `condition` (Excellent / Good / Fair) per Policy Bible §3.2 — for the two mobile-asset classes it's required; for spaces it's replaced by free-text condition notes.

**Universal listing fields** (outside `specs`, all classes): title, description (≥50 chars), asset_class, asset_type, photos 1–10, yard/location, daily price (required), weekly/monthly price (optional), unit_count, availability notes.

---

## 2. Plant & Machinery

**Class-common specs**

| Field | Kind / unit | Req | Notes |
|---|---|---|---|
| make | text | ✔ | e.g. Caterpillar, Komatsu, XCMG |
| model | text | ✔ | e.g. 320D |
| year | number | ✔ | Year of manufacture |
| condition | select: Excellent/Good/Fair | ✔ | |
| operating_weight | number, tonnes | — | ★ filterable (min/max) |
| engine_power | number, hp | — | |
| hours_logged | number, hrs | — | Hour-meter reading at listing time |
| fuel_type | select: Diesel/Petrol/Electric/Hybrid | — | |
| operator_included | select: Included / Available (extra) / Not available | ✔ | Drives PB §12.2 acknowledgment + operator fields below |
| operator_day_rate | number, ₦/day | if "Available (extra)" | |
| operator_experience | number, years | — | |
| certifications | text | — | Free text MVP; doc upload Phase 3 |

**Type-specific specs** (asset types in MVP launch set)

| Asset type | Fields |
|---|---|
| Excavator | bucket_capacity (m³), max_dig_depth (m), boom_config (select: Standard/Long-reach), tracked_or_wheeled (select) |
| Bulldozer | blade_type (select: Straight/Universal/Angle), blade_width (m), ripper (boolean) |
| Wheel Loader / Backhoe | bucket_capacity (m³), lift_capacity (t) |
| Grader | blade_width (m) |
| Roller / Compactor | drum_width (m), drum_type (select: Smooth/Padfoot), vibratory (boolean) |
| Mobile Crane | max_lift_capacity (t) ★, boom_length (m), jib_length (m), crane_type (select: Truck-mounted/Rough-terrain/All-terrain/Crawler) |
| Tower Crane | max_lift_capacity (t), jib_length (m), max_height (m) |
| Boom / Scissor Lift | working_height (m), platform_capacity (kg), power (select: Diesel/Electric) |
| Forklift (industrial) | lift_capacity (t), lift_height (m), tyre_type (select: Pneumatic/Solid) |
| Concrete Mixer (transit) | drum_capacity (m³) |
| Concrete Pump | output (m³/h), boom_reach (m), pump_type (select: Boom/Line) |
| Generator | power_output (kVA) ★(within type), phase (select: Single/Three), soundproof (boolean), fuel_consumption (l/h) |
| Air Compressor | air_delivery (cfm), pressure (bar) |
| Drilling Rig | max_drill_depth (m), drill_diameter (mm), rig_type (select: Rotary/DTH/Piling) |
| Welding Machine | output (amps), power_source (select: Diesel/Electric) |

## 3. Trucks & Haulage

**Class-common specs**

| Field | Kind / unit | Req | Notes |
|---|---|---|---|
| make / model / year | text/text/number | ✔ | |
| condition | select: Excellent/Good/Fair | ✔ | |
| payload_capacity | number, tonnes | ✔ | ★ filterable |
| driver_included | select: Included / Self-drive allowed / Both options | ✔ | Drives acknowledgment; self-drive requires hirer licence disclosure |
| driver_day_rate | number, ₦/day | — | If driver optional-extra |
| insurance_cover | select: Comprehensive/Third-party/None disclosed | — | Displayed prominently |
| operating_range | select: Lagos only / South-West / Nationwide | ✔ | Where the truck will work |
| registration_state | text | — | Plate state; full plate number stays private (Ops-visible only) |

**Type-specific specs**

| Asset type | Fields |
|---|---|
| Tipper / Dump Truck | bucket_capacity (m³), axle_config (select: 6×4/8×4/10-tyre/12-tyre) |
| Flatbed Truck | deck_length (m), deck_width (m) |
| Box / Covered Truck | cargo_volume (m³), tail_lift (boolean) |
| Lowbed / Lowboy Trailer | deck_length (m), max_load (t), ramps (boolean) |
| Fuel / Chemical Tanker | tank_capacity (litres), compartments (number), product_class (select: PMS-AGO/Water/Chemical/Food-grade) |
| Water Bowser | tank_capacity (litres), pump (boolean) |
| Crane Truck (Hiab) | crane_capacity (t), crane_reach (m) |
| Reach Stacker / Container Handler | lift_capacity (t), stacking_height (containers), container_sizes (multi: 20ft/40ft/45ft) |
| Truck Head (tractor unit) | horse_power (hp), axle_config (select) |

## 4. Warehousing & Storage

**Class-common specs**

| Field | Kind / unit | Req | Notes |
|---|---|---|---|
| floor_area | number, sqm | ✔ | ★ filterable (min) |
| ceiling_height | number, m | ✔ | Clear height |
| loading_bays | number | — | |
| dock_levellers | boolean | — | |
| power_supply | select: None/Single-phase/Three-phase | ✔ | |
| backup_power | boolean | — | Generator on site |
| security | multi: Fenced/CCTV/Guards 24-7/Access control | ✔ ≥1 | |
| fire_safety | multi: Extinguishers/Hydrants/Sprinklers/Alarms | — | |
| floor_load_capacity | number, t/sqm | — | |
| office_space | boolean (+ sqm) | — | |
| truck_access | select: Trailer-accessible / Light truck only | ✔ | Road access reality |
| condition_notes | text | — | Replaces condition select for spaces |

**Type-specific specs**

| Asset type | Fields |
|---|---|
| Dry Warehouse | racking_installed (boolean), pallet_positions (number) |
| Cold Storage | temperature_range (select: Chilled 0–8°C / Frozen −18°C / Blast), cold_capacity (sqm or pallets), temperature_monitoring (boolean) |
| Bonded Warehouse | customs_licence_status (select: Active/Pending), licence_expiry (text, Ops-verifiable) |
| Distribution Centre | dock_doors (number), yard_space (boolean), cross_dock (boolean) |
| Self-Storage Unit | unit_size (sqm), climate_controlled (boolean), access_hours (select: 24-7/Business hours) |

## 5. Terminals & Container Yards

**Class-common specs**

| Field | Kind / unit | Req | Notes |
|---|---|---|---|
| total_area | number, sqm (display ha when >10,000) | ✔ | |
| container_capacity | number, TEU | ✔ | ★ filterable (min) |
| surface_type | select: Concrete/Interlocked/Asphalt/Compacted laterite | ✔ | |
| weighbridge | boolean | — | |
| reefer_plugs | number | — | 0 = none |
| gate_system | select: Manual / Automated / Gate + tally | — | |
| customs_status | select: Bonded / ICD-licensed / Non-bonded | ✔ | Trust-critical; Ops may verify |
| handling_equipment | multi: Reach stacker/Forklift/Empty handler/Crane/None — hirer brings own | ✔ ≥1 | |
| operating_hours | select: 24-7 / Day shift / Custom (text) | ✔ | |
| port_distance | number, km | — | Distance to nearest port gate |
| rail_access | boolean | — | |

**Type-specific:** Port Terminal adds berth_access (boolean), max_vessel_draft (m); ICD adds customs_examination_area (boolean); Container Yard / Bonded Depot use class-common only (MVP).

## 6. Land & Staging

**Class-common specs**

| Field | Kind / unit | Req | Notes |
|---|---|---|---|
| area | number, sqm (display ha when >10,000) | ✔ | ★ filterable (min) |
| surface_type | select: Concrete/Tarmac/Compacted laterite/Gravel/Bare earth | ✔ | |
| weight_bearing | select: Heavy plant OK / Light vehicles only / Unverified | ✔ | Honest-default option included deliberately |
| fencing | select: Fully fenced/Partially/Open | ✔ | |
| security | multi: Guards/CCTV/Lighting/None | — | |
| access_road | select: Trailer-accessible/Truck-accessible/Car only | ✔ | |
| utilities | multi: Power/Water/Drainage/None | — | |
| zoning | select: Industrial/Commercial/Mixed/Undetermined | — | |
| gradient | select: Level/Slight slope/Sloped | — | |
| condition_notes | text | — | |

**Type-specific:** Fabrication Yard adds covered_area (sqm), gantry_crane (boolean + capacity t); Laydown/Marshalling/Industrial Land use class-common only (MVP).

---

## 7. MVP Boundaries & Governance

- **Launch asset-type set** = the types named above (~35). "Other (describe)" exists per class — routes to Ops review before going Live, and tells us which types to add next.
- **MVP search filters:** class, price, distance, text + the ★ field per class (operating_weight; payload_capacity; floor_area; container_capacity TEU; area). Everything else is display-only until Phase 5.
- Templates carry a `version`; a listing stores the template version it was created under — edits migrate forward lazily. (TSD detail; flagged here so the FSD can reference it.)
- Spec values are supplier-asserted. Verification of trust-critical claims (customs_status, insurance_cover, certifications) is manual via Ops in MVP, badge-gated in Phase 3.

## 8. Sign-off
1. ✅/❌ The spec model (templates = server config, required-gates-publish, completeness score stored)
2. ✅/❌ Field sets per class (§2–§6) and the launch asset-type list
3. ✅/❌ One ★ filterable headline spec per class for MVP
