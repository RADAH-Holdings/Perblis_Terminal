# Wave 5 — Messaging: Conversations, Masking, Realtime

**Status:** ⏸ Gated on Wave 4 sign-off
**Depends on:** Wave 4 (hire conversations attach to hires; masking unlocks on payment)
**Spec references:** FSD §8 (messaging — incl. Acceptance checks) · §9 (new-message notification row) · TSD §3.1 (`messaging`), §3.3 (`conversations`, `messages`), §3.10 (masking implementation) · §4 (Ably realtime, D-011)

## Objective

Two-party conversations with permanent history: enquiry conversations (listing-level or storefront general) and hire conversations (auto-created at acceptance — wiring the Wave 4C stub), with server-side contact masking until the related hire is paid, Ably realtime fan-out, polling degradation, and unread counters. After this wave the platform conversation loop — enquire → request → accept → chat → pay → contact unlocks — is complete end-to-end.

## In scope

### 5.1 Conversations & messages
- `POST conversations` — enquiry kind: `listing_id` (one per listing+hirer, partial unique index) **or** `supplier_id` (storefront "general enquiry", no listing attached). Hire conversations are never client-created — they exist via the acceptance transition (replace the Wave 4C stub; backfill any stub-created gaps).
- `GET conversations` — rows per FSD §8: counterparty + badge, listing thumb + title (or "General enquiry"), yard name, last-message preview, timestamp, unread count. Aggregate unread badge in the payload.
- `GET conversations/:id/messages` (cursor) · `POST conversations/:id/messages` · `POST messages/read` (bulk mark-read).
- **Access: participants only; third parties get 404** (not 403 — no existence leak; FSD §8 acceptance). Ops visibility arrives with the dispute context (Wave 6).
- History permanent; no edits, no deletes.

### 5.2 Masking (TSD §3.10 — server-side, at write time)
- On create: regex Nigerian phones (`(\+?234|0)[789][01]\d{8}` **+ spaced/dotted variants**) and emails → `body_masked` stored alongside `body` (original retained for Ops/dispute).
- Serving rule: hire conversations serve `body` once the hire is **Confirmed or later**, else `body_masked`; **enquiry conversations always serve `body_masked`** — indefinitely. Unlock applies only to that hire's conversation (FSD §8 acceptance).
- No keyword surveillance beyond this regex (deliberate posture). Masked rendering style (`0803••• 🔒` + explainer) is a client concern — the API exposes a `masked: bool` flag per message so clients can show the notice.

### 5.3 Realtime (Ably, D-011 — TSD §4)
- `GET realtime/token` — Ably TokenRequest, capabilities scoped to the caller's own channels only: `conv:{id}` for their conversations, `user:{id}` for their badge/hire events.
- Server publishes via Ably REST inside `transaction.on_commit`: new message → `conv:{id}`; unread/badge deltas and **hire status changes** (retro-wiring Wave 4's transitions) → `user:{id}`.
- Postgres is the message of record; Ably is fan-out only. Degradation: clients poll at 15s when Ably is unavailable — the REST surface fully supports this (no realtime-only data). Dev without `ABLY_API_KEY`: token endpoint returns `not_configured`; everything works by polling.

### 5.4 Notifications
- FSD §9 "New message" row: realtime badge (no email). Unread counters transactionally correct under concurrent reads/sends.

## Out of scope (deferred)

- Push notifications (Phase 3) · typing indicators / delivery receipts (not in spec) · attachments in chat (not in MVP) · Ops conversation viewer UI (Wave 6).

## Contracts frozen at wave end

`conversations/*`, `messages/read`, `realtime/token` — consumed by portal `/messages` (Wave 7) and the app's Messages tab (Wave 8).

## Mandatory tests (FSD §8 acceptance checks as named tests)

- Masking matrix: phone formats (`0803…`, `+234…`, `234…`, spaced, dotted) and emails caught; benign numerics (prices, quantities, RC numbers) **not** mangled.
- Pre-payment hire conversation masked → same conversation unmasked after Confirmed → a *different* hire's conversation between the same parties stays masked.
- Enquiry conversations: masked forever, including after an unrelated hire between the parties confirms.
- 404 (not 403) for non-participants; supplier of the listing can't read another supplier's enquiries.
- One-enquiry-per-(listing, hirer) uniqueness; storefront general enquiry has no listing.
- Hire conversation auto-created exactly once at acceptance (idempotent under retried transitions).
- Unread counts: per-conversation + aggregate, race-tested (concurrent send + read).
- Ably token capability scoping (token for user A cannot subscribe `conv:` of a conversation A isn't in).
- Polling parity: full conversation state retrievable with Ably disabled.

## Exit criterion (founder demo)

> **Two devices/sessions in realtime chat on production**: an enquiry conversation shows a masked phone number with the explainer flag; the hire is accepted and paid (Paystack test mode); the hire conversation unmasks while the enquiry conversation stays masked. Pulling the Ably key degrades to 15s polling with zero message loss.

## Wave-end checklist

- [ ] FSD §8 acceptance checks pass as named tests
- [ ] Ably usage alert wired into weekly digest inputs (70% of free tier, TSD §4)
- [ ] OpenAPI regenerated & committed
- [ ] Founder approval recorded before Wave 6 begins
