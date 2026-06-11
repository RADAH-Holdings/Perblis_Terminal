# Wave 0 — Foundation: Monorepo, Skeleton, CI, First Deploy

**Status:** ⏸ Awaiting founder approval
**Depends on:** — (first wave)
**Spec references:** TSD §1 (topology) · §2 (repo, environments, CI/CD) · §3.1 (`core` app ownership) · design.md §3–§5, §8 · DECISIONS D-009…D-013

## Objective

A deployed, empty-but-healthy system: the monorepo exists with all four workspaces, the Django skeleton runs locally via docker-compose and in production on Railway, the portal serves hello-world on Cloudflare Workers, the tokens package builds, and CI gates every PR. Nothing domain-specific yet — but every later wave lands on rails laid here.

## In scope

### 0.1 Monorepo scaffold

- Layout exactly per TSD §2.1: `backend/` `portal/` `app/` `packages/tokens/` `docker-compose.yml` `.github/workflows/`.
- `docker-compose.yml`: `postgis:17-3.5` + `mailpit` (dev mail at [http://localhost:8025](http://localhost:8025)).
- Root `.gitignore` already covers the stack (verify, don't rewrite).

### 0.2 Django skeleton (`backend/`)

- Django 6.0.x · DRF 3.17 · `pyproject.toml` with uv-compatible deps; ruff config (lint + format) lives here.
- Settings split `settings/{base,dev,prod,test}.py` via django-environ; `.env.example` exhaustive per TSD §2.2 var table (every var listed, dummy values).
- **Custom `User` model in `accounts` — migration 0001, before anything else touches the DB.** Fields per TSD §3.3 `users` row (email citext unique, phone unique E.164, role flags, `account_level`, suspension/soft-delete fields). Auth *flows* are Wave 1; the model must exist now or it can never be swapped in.
- `core` app: `BaseModel` (UUIDv7 PK, `created_at`/`updated_at`), `core.money` (`kobo()`, `naira()`, `display()` — integer kobo only), permission stubs (`IsSupplier`, `IsHirer`, `IsVerified`), cursor pagination class, error-envelope exception handler (`{"error":{"code","message","fields?"}}`), `/healthz` (app + DB) and `/readyz` (DB · R2 · Ably auth · Paystack ping — each check degrades to "not configured" in dev, never crashes).
- drf-spectacular wired; `/api/docs/` serves an (empty) schema.
- django-tasks installed; worker entrypoint (`manage.py db_worker`) runs; one no-op heartbeat task proves the DB broker round-trip.
- structlog JSON logging; Sentry SDK wired (no-op without DSN).
- Missing-key fallback posture (design.md commandment 10): absent Termii/Resend/Ably/Paystack keys log to console — boot never fails on a missing integration key.

### 0.3 Tokens package (`packages/tokens/`)

- Token source JSON per design-system chapter 10; build script emits `tailwind.tokens.js` + `tokens.ts` (+ `glyphs/`). `pnpm build` is the contract; portal and app consume the artifacts, never the source.

### 0.4 Portal hello-world (`portal/`)

- Next.js 15 App Router via `@opennextjs/cloudflare`; Tailwind themed from `packages/tokens`; one page rendering brand name + token-driven color proving the pipeline; `wrangler.toml` checked in; deployed to Workers.

### 0.5 CI/CD (`.github/workflows/`)

- `backend.yml` (path-filtered): ruff check + format check · mypy (loose) · pytest against a PostGIS service container · `.env.example` completeness check (fails if settings reference an env var missing from the example).
- `portal.yml` (path-filtered): eslint · tsc · build.
- Coverage gates configured from day one (85% `hires`+`payments`, 70% overall) — trivially green now, binding later.
- Deploy: merge to `main` → Railway auto-deploy (api + worker; release phase runs `migrate`) · portal deploy via wrangler action.

### 0.6 Railway production environment

- Project with three services per TSD §1: `api` (gunicorn, 512MB), `worker` (django-tasks runner, 256MB), PostgreSQL 17 + PostGIS 3.5. Env vars set; `DEBUG=0`; `SECRET_KEY` generated, never committed.
- Cloudflare R2: create `public` + `private` buckets; creds in Railway env (presign service implemented Wave 2, creds wired now).
- Budget check after deploy: projected fixed spend ≤ $25/month (target ≈ $10–15, TSD §0/04 §8).

## Out of scope (deferred)

- Auth endpoints, OTP, JWT (Wave 1) — only the User *model* lands now.
- Any domain model beyond User (Waves 2–5) · R2 presign endpoint (Wave 2) · Ably token endpoint (Wave 5) · Expo app scaffold (Wave 8 unless trivially included; not an exit criterion).

## Mandatory tests

- `core.money` round-trips and display formatting (`display(125000000) == "₦1,250,000"`); kobo helpers reject floats.
- Error envelope shape on a forced 400/404/500.
- `/healthz` green with DB up; degraded payload with a check failing (simulated).
- Heartbeat task enqueued → executed by worker (integration, against compose).
- CI proves itself: the PR that adds the workflows must pass them.

## Exit criterion (founder demo)

> `/healthz` returns green **in production** on Railway, and the portal hello-world page loads **on Cloudflare Workers**. CI is green on `main`. `docker compose up` + `runserver` + `db_worker` works from a fresh clone using only README/design.md instructions.

## Wave-end checklist

- [ ] Fresh-clone dev setup verified (the design.md §8 commands work verbatim)
- [ ] `.env.example` exhaustive; CI check enforcing it
- [ ] Custom User migration 0001 applied in prod
- [ ] No secrets in git history
- [ ] Founder approval recorded before Wave 1 begins