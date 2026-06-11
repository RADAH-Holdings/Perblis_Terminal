# 01 · Cross-Surface Flows
Branch-complete definitions. Notation: `[screen]` · `(decision)` · `{state change}` · → step. Every flow names its error/abandon branches — unnamed branches are bugs.

## F1 · Registration & OTP (app + portal)
`[Auth]` email+name+phone+password → submit → `{user created}` → `[OTP]` 6-cell input, 10:00 expiry mono countdown, resend (3/hr)
- (code ok) → portal: role intent → checklist · app: `[Onboarding]` → `[Map]`
- (wrong ×3) → cooled-down retry copy → (expiry) → resend prompt
- (phone already registered) → inline error + "Sign in instead" link
- Abandon mid-OTP: account exists unverified; next login resumes OTP step.

## F2 · Identity verification
`[Profile/Settings → Verify]` → doc-type select → camera/file → preview (retake) → submit → `{VerificationRequest pending}` → "12h SLA" state
- (approved) → email + badge update + any blocked intent resumes (publish, >₦250k request)
- (rejected) → reason shown → resubmit loop (max 3 before support handoff copy).
Gate integration: triggered contextually from publish-block (supplier) and cap-block (hirer) — never a dead-end error.

## F3 · Request → Pay (the revenue path)
`[Listing Detail]` → Request to hire → `[Dates]` (held dates blocked; AvailabilityStrip) → `[Review]` PricePreview + note + acknowledgments → submit
- (409 race) → "dates just taken" sheet → refreshed strip → re-pick
- (Basic cap exceeded) → gate sheet → F2 or reduce dates
→ `{Requested}` → `[Hire Detail]` "Awaiting supplier — {countdown 24h}"
- (declined) → reason + similar-listings row
- (expired 24h) → "supplier didn't respond" + re-request CTA
- (accepted) → `{Accepted}` notify → **Pay now** → Paystack (expo-web-browser / portal link) → return → client polls hire status (webhook is truth)
  - (success) → `{Confirmed}` → stamp moment + receipt + conversation unmasks
  - (failed) → mapped reason + "{n} attempts left" + countdown persists
  - (window expiry / 3 fails) → `{Cancelled system}` → dates released copy → re-request CTA
- Hirer cancel allowed at any pre-payment point (no penalty, confirm dialog).

## F4 · Accept / Decline (supplier)
`[Hires table]` Requested row → `[Hire Detail]`: hirer profile (level badge, history count), LockedTerms-estimate, dates vs calendar inline strip
- Accept → (operator/driver included?) acknowledgment checkbox → confirm → `{Accepted}` → "Awaiting payment" + payment-window note
- Decline → reason (select + free text, required) → `{Declined}`
- (no action 24h) → `{Expired}` — surfaced in supplier's list with accountability copy (3 expiries in 30d → dashboard warning banner; PB no-show ladder feeds Ops).

## F5 · Cancellation & refund (post-payment)
Either party → Cancel → **refund preview manifest** (rule applied per FSD §6.6, exact figures) → typed confirm? No — double-confirm dialog (type-to-confirm is Ops-only) → `{Cancelled by}` → refund `{pending}` → Paystack → `{completed}` (tracked row in hire detail; email both)
- Supplier cancel adds: evidence note field (penalty-free categories listed) + strike notice copy
- (refund API failure) → Ops alert + hirer sees "refund processing — 5 business days" fallback copy.

## F6 · Handover (on-hire & off-hire)
Trigger surfaces: hire detail banner (start/end day), Hires tab prompt chip
`[HandoverCapture]` photos per class checklist → reading (if class requires) → notes → submit → `{record created, party A confirmed}` → counterparty notified → their `[ConfirmPanel]` review → confirm `{both confirmed}` → status advances (`On Hire` / `Completed`)
- (counterparty disputes content) → re-capture loop once, then "raise dispute" path
- (nobody documents) → auto-advance at +24h/+48h with no-record flag.

## F7 · Enquiry & messaging
Entry: Listing Detail "Enquire" (listing context) · Storefront "Message" (general)
→ conversation exists? reuse : create → `[Conversation]` MaskedContact active → messages (optimistic send, grey→confirmed tick)
- (hire reaches Confirmed) → unmask + system message "Contact details unlocked"
- (Ably down) → polling fallback, no UI difference beyond latency.

## F8 · Role activation (hirer → supplier, in-app)
`[Profile]` "Become a supplier" → explainer screen (portal is the supplier surface) → "Email me the link" → magic-link email → portal onboarding checklist (F1-equivalent state already authed). App never half-implements supplier tools.

## F9 · Listing lifecycle (supplier)
Create (6 steps, per-step draft save) → publish gates: required specs ✓, ≥1 photo ✓, location ✓, account Verified ✓ → `{Live}` toast "on the map"
- Pause (instant, undo-toast 6s) · Edit (live edits don't touch locked hires — banner reminder) · Archive (confirm; irreversible copy) · Duplicate (new draft, photos optional copy).

## F10 · Report listing
`[Listing Detail]` overflow → reason select → optional detail → submit → SLA copy. Reporter sees no further state (anti-gaming); Ops queue handles (J7).

## F11 · Payout (supplier-visible slice)
`{Completed}` → payout row `pending→due` on portal dashboard ("queued — payouts run weekly") → founder marks paid → `{paid}` + email with reference → figure reconciles with hire detail manifest. (frozen) state shows "on hold — dispute" copy.

## F12 · Session & auth maintenance
Token refresh silent; (refresh expired) → re-auth sheet preserving screen intent; logout clears SecureStore/cookies + Ably detach; suspended account → blocking screen with support contact (no silent failures).
