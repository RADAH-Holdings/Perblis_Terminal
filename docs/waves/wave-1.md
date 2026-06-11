# Wave 1 — Accounts: Identity, Auth, Verification

**Status:** ⏸ Gated on Wave 0 sign-off
**Depends on:** Wave 0 (User model, core plumbing, CI, prod deploy)
**Spec references:** FSD §4 (users, roles, verification — incl. its Acceptance checks) · TSD §3.1 (`accounts`), §3.3 (`users`, `otp_codes`, `verification_requests`), §3.8 (auth endpoints + throttles), §3.9 (private-bucket media) · DECISIONS — none specific; lexicon per doc 02

## Objective

A real person can register, verify their phone with a real SMS OTP, log in with JWT, reset their password, activate the supplier role, and submit identity/business verification documents that land in an Ops review queue. Account levels (Basic / Verified / Business Verified) exist and gate nothing yet — the gates arrive with the features they protect (publish in Wave 2, hire cap in Wave 4).

## In scope

### 1.1 Registration & OTP (FSD §4.2)
- `POST /api/v1/auth/register` — full name, unique email, unique Nigerian phone (normalise to E.164), password policy ≥8 chars + 1 uppercase + 1 number. Defaults: `is_hirer=True`, `is_supplier=False`, `account_level=basic`.
- OTP via **Termii** (design.md commandment 10: no key in dev ⇒ code prints to console; the flow itself is always real). 6 digits, hashed at rest, 10-min expiry, **3 resends/hour**, **5 verify attempts then a new code is required**. `POST auth/otp/verify` · `POST auth/otp/resend`.
- Welcome email via Resend (dev ⇒ mailpit). ToS/Privacy consent captured at registration (NDPR, FSD §12).

### 1.2 Login, JWT, reset (FSD §4.2)
- `POST auth/login` (email+password) → simplejwt access **60 min** + refresh **7 days, rotating, blacklist on logout**. JWT claims: `user_id, is_supplier, is_hirer, account_level, is_active`.
- Lockout: 5 failed logins / 15 min / IP. Throttles per TSD §3.8 (OTP send 3/h/phone · login 5/15min/IP).
- `POST auth/token/refresh` · `POST auth/logout` (blacklists refresh).
- Password reset: `POST auth/password-reset` (always 200, no enumeration) → single-use emailed link, 1-hour expiry → `POST auth/password-reset/confirm` invalidates all sessions.

### 1.3 Me & roles
- `GET/PATCH /api/v1/me` (name, avatar via presign — presign endpoint itself lands Wave 2; avatar can slip to Wave 2 without blocking exit).
- `POST me/activate-supplier` — flips `is_supplier`; the *business-profile completeness* gate on going Live is enforced in Wave 2 where listings exist.

### 1.4 Verification (FSD §4.3 — real-but-manual)
- `POST me/verification` — kind `identity` (NIN slip / passport / driver's licence / voter's card) or `business` (CAC certificate + RC number). JPEG/PNG/PDF ≤5MB → **private R2 bucket**, keys in `verification_requests.doc_keys`. One pending request per kind.
- `GET me/verification` — current level + request states + rejection reasons.
- Ops queue: Django Admin list (pending first), inline doc viewer via 15-min presigned GETs, approve → level upgrade, reject → **mandatory reason**, user notified (badge + email), resubmission allowed. Full Ops Console UX is Wave 6 — this wave ships the functional minimum so verification is operable from day one.
- Suspension semantics (FSD §4.2): suspended user fails login with a stable error code; soft-delete fields honoured by auth.

## Out of scope (deferred)

- Publish gate (Wave 2) · ₦250k Basic hire cap (Wave 4) · storefront badge rendering (Wave 2/7) · 2FA on admin (hardening config, verify in Wave 6) · push notifications (Phase 3).

## Contracts frozen at wave end

`auth/*`, `me`, `me/activate-supplier`, `me/verification` schemas published at `/api/docs/` — the portal (Wave 7) and app (Wave 8) build their auth flows against this freeze.

## Mandatory tests

- OTP: expiry, resend throttle (3/h), attempt exhaustion (5 → new code required), hash-at-rest (no plaintext codes in DB).
- JWT: rotation, blacklist-on-logout, claims content; suspended/soft-deleted users rejected at login *and* at token refresh.
- Lockout and throttle behaviour (freezegun).
- Password reset: single-use, 1-h expiry, session invalidation, no user enumeration.
- Verification: private-bucket keys **never** publicly reachable (FSD §4.3 acceptance check); approve/reject transitions + notification dispatch; rejected user sees reason and can resubmit.
- Lexicon sweep: no `owner`/`renter` identifiers (design.md commandment 1).

## Exit criterion (founder demo)

> On the **production** API via `/api/docs/`: register → receive real OTP → verify → login → submit an ID document → approve it in admin → `GET me/verification` shows **Verified**. Coverage gates green.

## Wave-end checklist

- [ ] FSD §4.3 acceptance checks pass as named tests
- [ ] OpenAPI regenerated & committed; auth contract frozen
- [ ] Termii + Resend live keys in Railway env; dev fallbacks verified
- [ ] Founder approval recorded before Wave 2 begins
