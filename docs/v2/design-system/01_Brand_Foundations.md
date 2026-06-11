# 01 · Brand Foundations

## 1. Identity

**Name:** Terminal — always set in full; never "TML", never lowercase in lockups.
**Wordmark:** `TERMINAL` in Archivo Expanded SemiBold, +8% tracking, all-caps. Two approved lockups:
1. **Plate** (primary): amber wordmark on ink-900 rounded plate (r-sm) — the equipment data-plate. Used: app icon, portal nav rail, email header.
2. **Inline** (secondary): ink-900 wordmark on light surfaces; amber tick-bar (4×18px vertical bar) preceding it as the brand accent.

**Clear space:** the height of the "T" on all sides. **Minimum size:** 88px wide (plate), 64px (inline).
**Symbol** (favicon/app icon at small sizes): the **T-crane glyph** — a "T" whose arm extends right like a tower-crane jib, amber on ink. One glyph, drawn once, in `packages/tokens/glyphs/brand/`.

**Misuse (hard rules):** no gradients in the lockup · no amber-on-white wordmark (fails contrast) · no stretching, outlining, or shadowing · never placed over photography without the ink scrim (§5).

## 2. Signature Motifs — what makes Terminal *look like Terminal*

Four ownable details. Restraint rule: **maximum one motif per screen**, except receipts (stamp + manifest allowed).

### M1 · The Hazard Stripe
45° diagonal stripe band, amber-500/ink-900 alternating, 8px pitch, used at 4px height as a **section punctuation line** — never as a container border. Where: onboarding headers, splash footer, empty-state baselines, the top edge of the Ops Console, marketing/email dividers. CSS: `repeating-linear-gradient(45deg, #F59E0B 0 8px, #16181D 8px 16px)`; height 4px; full-bleed.

### M2 · The Manifest Block
Document-styled panels: paper-0 surface, hairline rules between rows (`0.5px ink-200`), row labels in Inter, values in Plex Mono right-aligned, a heavier rule (`2px ink-900`) above the total row. Where: LockedTerms, receipts, payout statements, spec tables in "document" contexts. This is the visual voice of "contract you can trust."

### M3 · The Stamp
A rotated (−6°) rounded-rect outline stamp, 2px border, uppercase Archivo letter-spaced label — like a customs stamp. Colors: `PAID` amber border/text · `COMPLETED` green · `CANCELLED` red · `VERIFIED` blue. Where: receipts, completed-hire detail headers, Ops-resolved disputes. Appears with the stamp motion (08 §4). Never on cards/lists — detail surfaces only.

### M4 · Corner Registration Marks
Thin L-shaped crop marks (1.5px, 12px arms) on the four corners of **hero imagery only** (storefront cover, listing gallery first photo, onboarding illustrations) — evoking container ID plates and technical drawings. ink-900 at 60% on photos, ink-200 on light fields. Never on thumbnails.

## 3. Art Direction

**The feeling:** golden-hour at a working port — warm light on steel. Heavy Duty is warm-industrial, not brutalist: warm paper (#F7F7F5), warm amber, photography full of dust and diesel, set in rigorous structure.

**Composition habits:** generous top whitespace on detail screens; oversized Plex Mono numerals as visual anchors (dashboard stats, price headers — up to 40px); strict left-edge alignment columns ("everything hangs from the rail"); full-bleed photography balanced by dense data blocks below.

## 4. Photography

Supplier-uploaded photos are the product's primary imagery — the system's job is making *real, imperfect* photos look intentional:
- **Containers:** 4:3 thumbnails, 16:10 galleries/heroes, center-crop with face/subject detection off (machines, not people).
- **Treatment:** none in-product (no filters on listing truth). A `+12%` contrast / slight warm cast is applied **only** to marketing/storefront *cover* images, never gallery evidence photos.
- **Scrim:** any text over photography sits on `linear ink-900 0%→55%` bottom scrim; minimum 4.5:1 measured at the text position.
- **Brand/marketing photography** (site, onboarding, empty-state heroes when real photos exist): duotone ink-900/amber-500 treatment — the one place the brand gets cinematic.
- **Forbidden:** stock smiling-people-in-hardhats; watermarked images (blocked at upload per Policy Bible §3.3); AI-generated equipment photos.

## 5. Illustration

Used **only** where there is no real thing to photograph: empty states, onboarding explainers, error pages, verification pending.
- **Style:** single-weight 2px line drawings in ink-300, one amber-500 accent element per illustration (e.g., the load on a line-drawn crane), on transparent. Isometric 30° for machines/spaces; flat front-on for documents/UI concepts.
- **Cast:** machines, yards, documents, map fragments — never human characters/mascots.
- Library starts with 12: empty map, no listings, no hires, no messages, verification pending, verification approved, payment pending, offline, error 500, not found, onboarding ×2. Stored as SVG in `packages/tokens/illustrations/`.

## 6. The Receipt as Brand Artifact

The paid-hire receipt is Terminal's business card — the thing that gets screenshotted into WhatsApp. It composes M2 + M3: plate lockup header, manifest ledger, PAID stamp, hire ID + dates in mono, perforated bottom edge (8px dashed rule + scissors-free), QR deep-link to the hire record. One design, three renders: in-app share-image, portal print/PDF, email. This artifact is specced fully in 06 §8.
