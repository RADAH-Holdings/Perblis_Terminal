# Build Waves — Index & Gating Rules

Terminal is built in **gated waves**. Each wave has its own file in this directory: the complete build brief a coding agent needs to execute that wave without re-deriving scope.

## The rules (binding — see design.md §7)

1. **No wave starts without explicit founder approval.** Finishing a wave does not authorize the next one.
2. A wave is **done** when its exit criterion is demonstrated, its mandatory tests are green, and its OpenAPI contracts (if any) are regenerated and committed.
3. Contracts frozen at the end of a wave are **breaking-change-locked** — later waves consume them; changing one requires founder sign-off.
4. If a wave surfaces a spec conflict or gap: **stop, surface it** for a DECISIONS.md entry. Never improvise around it.
5. Every PR inside a wave satisfies the Definition of Done (design.md §6).

## Backend waves (this batch)

| Wave | File | Deliverable | Status |
|---|---|---|---|
| 0 | [wave-0.md](wave-0.md) | Monorepo, compose, Django skeleton, tokens package, CI, prod deploy | ⏸ Awaiting founder approval |
| 1 | [wave-1.md](wave-1.md) | Accounts: register / OTP / JWT / reset · verification requests + queue | ⏸ Gated on Wave 0 |
| 2 | [wave-2.md](wave-2.md) | Supply: supplier profiles, yards, spec templates, listings CRUD + publish | ⏸ Gated on Wave 1 |
| 3 | [wave-3.md](wave-3.md) | Search: map endpoint (yard aggregation), list, filters | ⏸ Gated on Wave 2 |
| 4 | [wave-4.md](wave-4.md) | Hires + money: state machine, availability, fees, Paystack, sweeps, payouts | ⏸ Gated on Wave 3 |
| 5 | [wave-5.md](wave-5.md) | Messaging: conversations, masking, Ably + polling fallback | ⏸ Gated on Wave 4 |
| 6 | [wave-6.md](wave-6.md) | Ops Console: queues, dashboard, dispute actions, digests | ⏸ Gated on Wave 5 |

## Frontend waves (authored after backend wave files are approved)

| Wave | Deliverable | Notes |
|---|---|---|
| 7 | Supplier Portal complete (FSD §10.2) | May interleave with 5–6 once Wave 4 contracts freeze |
| 8 | Hirer app complete (FSD §10.1) | May interleave with 5–6 once Wave 4 contracts freeze |
| 9 | Hardening: load test, security pass, runbooks, beta onboarding | Launch gate = FSD §13 |

## Reading order for any wave

`design.md` → this README → the wave file → the FSD/TSD sections it cites → relevant `docs/v2/` companion docs.

## Status legend

⏸ gated · 🟡 approved & in progress · ✅ exit criterion demonstrated, founder signed off
