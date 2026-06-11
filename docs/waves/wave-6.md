# Wave 6 — Ops Console: The Founder's Cockpit

**Status:** ⏸ Gated on Wave 5 sign-off
**Depends on:** Waves 1–5 (every queue operates on objects built earlier; service functions for dispute/payout/verification actions already exist — this wave gives them surfaces)
**Spec references:** FSD §10.3 (Ops Console — normative surface list) · §11.5 (Ops weekly rhythm — the usability bar) · TSD §3.1 (`ops`), §3.5 (digests/reconciliation cadence), §7 (admin security) · design.md commandment 5 (every Ops action event-logged)

## Objective

The founder operates the entire marketplace from Django Admin **without ever opening a SQL console**: verification queue, payout batch, reports queue, dispute resolution, listing moderation, user management, reconciliation status, and the weekly digest. Wave 4/1 built the service functions; this wave builds the operator experience and locks down admin security.

## In scope

### 6.1 Admin hardening (TSD §7)
- Staff-only · **django-otp 2FA enforced** for all staff accounts · separate session cookie path · login IP logging · every action lands in `hire_events` (domain actions) and/or Django `LogEntry` (admin actions). Admin actions call the **same service functions** as the API — no parallel write paths (design.md commandment 8 applies to admin too).

### 6.2 Dashboard (FSD §10.3)
- Single ops landing page: GMV, fees collected, payout liability (sum of `due` + `frozen`), hires by state, new users (7d), reconciliation status (last run, mismatch count), pending queue counts (verification / payouts / reports / disputes). Read-optimized queries; no page > 2s.

### 6.3 Verification queue (upgrade of Wave 1 minimum)
- Pending-first list, filters by kind/state; inline doc viewer via 15-min presigned GETs; approve → level change; reject → mandatory reason; both notify (badge + email). SLA visibility: age column, >12h highlighted (FSD §4.3 SLA).

### 6.4 Payout queue (FSD §3.2)
- `due` payouts listed with supplier bank details (account number decrypted **for display here only**, masked elsewhere); mark-paid records the bank reference + timestamp → supplier "Payout paid" email (FSD §9). Freeze/unfreeze with reason. Batch ergonomics: filter by week, sum-selected total for the Friday batch (FSD §11.5).

### 6.5 Listings & reports moderation (FSD §5.2)
- Reports queue: open reports with reason, reporter, listing context, **sibling listings of the same supplier** (FSD §5.2); resolve as dismissed / warned / removed. Remove ⇒ reason required, listing → Removed, supplier notified, hire history preserved.
- Tier award (Basic → Verified/Inspected, manual in MVP) · pause/remove with reason · priority-review flag surfaced (3 reports/30d).

### 6.6 Hires admin & dispute resolution (FSD §7.3 row 7)
- Hire detail: full event timeline, both parties, financials, payment/refund/payout records, linked conversation (read-only — the Ops dispute-context visibility from FSD §8).
- Dispute resolution: → Completed **or** → Cancelled, with refund and/or payout adjustment amounts — flowing through `state.apply(ops, …)` + the Wave 4 service functions, every step event-logged. Admin cancel (any non-terminal state, reason required, refund rules applied).
- Money invariant surfaced: per-hire `collected − refunded − paid_out − retained_fee` shown; non-zero at a terminal state renders red.

### 6.7 Users admin
- Suspend (blocks login, hides listings + storefront, freezes payouts — assert the Wave 1/2/4 wiring end-to-end) / reactivate · strike management (manual adjust + reason) · internal notes · soft-delete state visibility.

### 6.8 Digests & reconciliation surfacing
- Weekly founder digest email (TSD §9): GMV, fees, hires by state, Ably usage (70% alert), R2 usage, queue ages. Reconciliation report page: daily run history, mismatches with drill-down. (Both tasks exist from Wave 4 — this wave completes their content and renders history.)

## Out of scope (deferred)

- Custom ops frontend (Django Admin **is** the MVP console — FSD §10.3) · bulk CSV exports beyond admin defaults · role-granular ops permissions (single-founder MVP; staff flag suffices) · automated moderation (Phase 3).

## Mandatory tests

- 2FA enforced: staff login without OTP device fails.
- Every ops mutation produces its event-log entry (parametrized across all actions).
- Dispute → Completed and → Cancelled paths: refund/payout adjustments correct, invariant holds at terminal state.
- Payout mark-paid: reference stored, email sent, state `paid`; freeze blocks mark-paid.
- Suspension cascade: login blocked + listings hidden from search + storefront 404 + payouts frozen — one test walking all four.
- Removed listing: reason required, supplier notified, hire history intact.
- Bank number: decrypted rendering only on the payout queue view; masked in every other admin surface.

## Exit criterion (founder demo — you are the test subject)

> On production, **you personally** work one item through every queue without SQL: approve a verification, pay a payout (test reference), resolve a report, resolve a dispute with a refund adjustment, suspend and reactivate a user — and the weekly digest email arrives with real numbers. Anything that forced you into a shell fails the wave.

## Wave-end checklist

- [ ] Every FSD §10.3 surface exists and was exercised in the demo
- [ ] 2FA live for all staff accounts in prod
- [ ] Runbooks drafted in `docs/runbooks/`: payout batch · refund handling · dispute resolution (TSD §9 — start now, harden in Wave 9)
- [ ] **Backend complete.** OpenAPI for the full API regenerated & committed
- [ ] Founder approval recorded before Wave 7 (portal) begins — Wave 7/8 files authored at that gate
