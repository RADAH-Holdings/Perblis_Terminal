# Terminal v2 — Stage 3: Architecture & Technology Stack
v0.1 DRAFT for founder review · June 2026
Constraint: **max $25 USD/month** total development/infra spend.
Research: live pricing verified June 2026 against official sources (links throughout).

---

## 1. Verdicts on the Locked Decisions (from founder's architecture doc)

| Locked decision | Research verdict |
|---|---|
| Django | ✅ **Confirmed.** Django 6.0.x is current (6.0.6, June 2026); GeoDjango remains the killer argument for this product. |
| Django built-in Admin | ✅ Confirmed (Ops Console foundation). |
| GeoDjango + PostGIS | ✅ Confirmed. PostGIS available on every candidate host (Railway via template, Render via `CREATE EXTENSION`, Supabase one-click, self-host trivially). |
| Cloudflare R2 | ✅ Confirmed. 10GB free, zero egress fees — uncontested at this budget. |
| **Django Ninja** | ⚠️ **Recommend override → DRF.** See §2. |
| **Celery + Redis** | ⚠️ **Recommend override → Django 6 Tasks + django-tasks DB worker (no Redis).** See §3. |
| **Pusher** | ⚠️ **Recommend override → Ably.** See §4. |

## 2. API Framework: DRF over Ninja (recommendation)

The 2025 "DRF is dying" narrative **aged poorly**: DRF shipped 3.16.1 (Aug 2025), **3.17.0 (Mar 2026), 3.17.1 (Mar 2026)** with Django 6 + Python 3.14 support ([release notes](https://www.django-rest-framework.org/community/release-notes/)). drf-spectacular: active. **rest_framework_gis: v1.2.1 May 2026** (OpenWISP-maintained).

The case, specific to Terminal:
1. **GIS is the product.** drf-gis gives `GeometryField`/GeoJSON serialization for PostGIS PointFields out of the box. **Ninja has no GIS ecosystem at all** — `ModelSchema` can't auto-map PointField; you hand-roll Point ⇄ GeoJSON conversion with zero community support. For a map-first product, the framework with the maintained GIS layer wins.
2. **Bus factor.** Ninja remains effectively one maintainer (a 2025 critique spawned the django-shinobi fork; backlog improved since but structure unchanged), and the Ninja JWT/extra packages are a *second* bus-factor-1 dependency. DRF + simplejwt (Jazzband) + spectacular is a multi-maintainer ecosystem with ~800k dependent repos.
3. **AI-agent leverage.** This codebase will be written largely by agents. DRF has a decade of training data and rigid conventions — agents produce more correct DRF with less supervision. (Loopwerk's hands-on comparison found DRF's ModelViewSet did in 4 lines what Ninja needed 30+ for, on exactly our CRUD-heavy shape.)
4. Ninja's real advantages — Pydantic ergonomics, async, serialization speed — don't bind here: the bottleneck is PostGIS queries, not serialization.

**Recommended:** Django 6.0.x · DRF 3.17 · simplejwt · drf-spectacular · rest_framework_gis.

## 3. Background Tasks: drop Redis entirely (recommendation)

**Celery+Redis is overkill for MVP workloads** (emails, hire-expiry sweeps, webhook retries, payment reconciliation) and Redis is a real line item everywhere: Render Redis paid = $10/mo; Upstash free tier has a confirmed trap — **an idle Celery worker's polling alone can burn the 500K free commands/month** ([Upstash docs](https://upstash.com/docs/redis/integrations/celery), [celery#6625](https://github.com/celery/celery/issues/6625)).

**Django 6.0 shipped the native Tasks framework** (DEP 14: `@task` + `.enqueue()`); [django-tasks](https://github.com/RealOrangeOne/django-tasks) provides the DB-backed worker. Postgres is the broker — no Redis, one fewer service, and we're on Django core's official trajectory. Scheduled jobs (expiry sweeps, reconciliation) via cron-style invocation or django-tasks' scheduling. Fallback if friction: django-q2 (same no-Redis property). Celery returns post-MVP only if we need rate-limited queues or heavy fan-out.

## 4. Realtime: Ably over Pusher (recommendation)

| | Pusher free | Ably free |
|---|---|---|
| Messages | 200k/day | 6M/month |
| **Concurrent connections** | **100** | **200** |
| Paid cliff | **$49/mo** | $29/mo |

Ably wins every axis ([Pusher](https://pusher.com/channels/pricing/), [Ably](https://ably.com/pricing)). The binding constraint for a map-first app (every open session may hold a socket) is concurrent connections — 100 is brushable at MVP top-end; 200 is not. Architecture is identical either way (server-issued tokens, channel per conversation), and the v1 build already proved the Ably pattern. Self-hosted Channels/Centrifugo rejected: adds websocket infra to a solo-founder ops surface to save $0.

## 5. Maps: MapLibre + OpenFreeMap (recommendation, decided by ToS not price)

- **Mapbox** is $0 at our scale (25k mobile MAU, 50k web loads, 100k geocodes free) **but**: requires card on file, and **Temporary Geocoding results may not be stored permanently** — storing listing coordinates from geocoded addresses (our core write path!) requires paid Permanent Geocoding. That ToS trap sits exactly on our product.
- **MapLibre GL** (web: drop-in mature; mobile: [maplibre-react-native](https://github.com/maplibre/maplibre-react-native) v11 — official MapLibre org project, RN New Architecture + Expo config plugin) + **[OpenFreeMap](https://openfreemap.org/)** tiles: $0, no key, commercial use explicit. Risk: donation-funded, no SLA → **mitigation: Protomaps fallback** — Nigeria PMTiles extract self-hosted on R2 ≈ $0 at our scale (~$11/mo even at 10M tiles); MapLibre swaps tile URLs without code changes.
- **Geocoding: [LocationIQ](https://locationiq.com/pricing) free** — 5,000 req/day, 2 req/sec, autocomplete allowed, commercial OK with attribution link. (Nominatim public API forbids autocomplete; MapTiler/Stadia free tiers forbid commercial use.) Note: street-level geocoding in Nigeria is weak on *all* providers — UX should lean on pin-drop + landmark/area entry, not address-string faith.

## 6. Hosting

**Web (Supplier Portal, Next.js): Cloudflare Workers — $0.** Vercel Hobby **explicitly forbids commercial use** — a marketplace on it is a ToS violation; Pro is $20/mo (most of the budget). [@opennextjs/cloudflare](https://opennext.js.org/cloudflare) is the official, production-ready path in 2026 (Next 15/16), free tier 100k req/day, commercial allowed.

**Backend (Django + worker + PostGIS): Railway — recommended.**

| Option | $/mo | Trade-off |
|---|---|---|
| **Railway Hobby** (web 512MB + django-tasks worker 256MB + [PostGIS template](https://railway.com/deploy/postgis-17) 512MB+1GB vol) | **~$10–15** | Managed, per-second billing, deploy-from-GitHub; set a usage cap. Familiar from v1. |
| Hetzner CX22 (4GB) + Dokploy/Coolify, everything self-hosted | ~$5–7 | Cheapest; founder becomes DBA/ops (backups, security, upgrades). ~150ms from Nigeria (EU). |
| Render (web $7 + worker $7 + Postgres $7) | ~$21 | Predictable but eats the budget; paid Redis would blow it ($31). |

Rejected: Fly.io (managed Postgres $38/mo; DIY everything otherwise), Supabase free as primary DB (**pauses after 7 days inactivity** — production-fragile), Neon (scale-to-zero cold starts; always-on ≈ $19/mo).

**Mobile builds: $0** — local Android builds (free, unlimited) + EAS free tier's **15 iOS cloud builds/month** (no Mac needed) + free EAS Submit; expo-updates OTA for JS-only changes to conserve iOS builds.

## 7. Nigeria Operational Costs (verified)

| Service | Cost | Notes |
|---|---|---|
| **Paystack** collections | 1.5% + ₦100, **capped ₦2,000**; ₦100 waived < ₦2,500 | Cap is a gift for heavy-asset tickets: collecting ₦5M costs ₦2,000 (0.04%). Push local cards/transfer — international cards are 3.9% **uncapped**. |
| Paystack refunds | Refund free, **but transaction fee NOT returned** | ≈ ₦2,000 cost per big-ticket refund — already covered by our ~1.5% processing deduction in the cancellation rules (03 §6). |
| Paystack go-live | **Starter (no CAC): collection caps + NO transfers** | MVP payouts are manual bank transfers (not Paystack Transfers), so Starter works at launch — but **CAC registration should be in motion before launch** for caps + Phase 2 rails. |
| **Termii** SMS OTP | ~₦16/SMS | Local aggregators (BulkSMS Nigeria etc.) run ₦2–7/SMS. Strategy: Termii's clean API first; 1,000 OTPs ≈ ₦16k (~$11) — if volume bites, swap aggregator behind the same interface, or email-OTP fallback at ₦0. |
| **Resend** email | Free 3,000/mo, 100/day | Brevo free (300/day ≈ 9k/mo) as fallback. |
| **Sentry** | Free: 5k errors/mo, 1 user | Fine for MVP; GlitchTip self-host later if needed. |

## 8. The Recommended Stack (one table)

| Layer | Choice | $/mo |
|---|---|---|
| Backend | Django 6.0.x + **DRF 3.17** + simplejwt + drf-spectacular + **rest_framework_gis** | — |
| Tasks | **Django 6 Tasks + django-tasks** (Postgres broker, no Redis) | $0 extra |
| DB | PostgreSQL 17 + PostGIS 3.5 (Railway template) | in Railway |
| Hosting (API+worker+DB) | **Railway Hobby** | ~$10–15 |
| Media | Cloudflare R2 (10GB free; KYC docs in private bucket, pre-signed URLs) | $0 |
| Realtime | **Ably free** (6M msg/mo, 200 conns) | $0 |
| Maps | **MapLibre GL** (web + maplibre-react-native) + **OpenFreeMap** tiles (+ Protomaps-on-R2 fallback) | $0 |
| Geocoding | LocationIQ free (attribution) + pin-drop-first UX | $0 |
| Supplier Portal | Next.js on **Cloudflare Workers** (@opennextjs/cloudflare) | $0 |
| Hirer app | React Native + Expo; local Android builds + EAS free iOS | $0 |
| Payments | Paystack (collect-only per D-006) | revenue-linked |
| SMS / Email | Termii / Resend free | usage (~$5–11) |
| Errors | Sentry free | $0 |
| **Total fixed infra** | | **~$10–15 / month** ✅ |

Headroom ≈ $10/month — absorbs Railway usage creep, SMS volume, or the Protomaps fallback if OpenFreeMap degrades.

## 9. Architecture Principles (carried into TSD)

1. Custom `User` model from migration 0001 (founder doc — confirmed best practice).
2. **Service-layer pattern**: business logic in `services.py` modules; views stay thin; the hire state machine and fee math live in one importable, unit-tested place.
3. API contracts: DRF serializers + drf-spectacular schema published at `/api/docs/` before frontend work on each module.
4. Webhooks (Paystack) are the system's load-bearing wall: idempotent handlers, signature verification, replay tolerance, daily reconciliation task.
5. Observability first: Sentry + structured logging + `/healthz` from Wave 0.
6. Monorepo layout decision deferred to TSD (backend / portal / mobile).

## 10. Founder Decisions Required
The four stack questions (framework, tasks, realtime, hosting) override or confirm the locked doc — asked via decision prompts. Maps recommendation (§5) stands unless objected to; switching map SDKs later is *not* cheap on mobile, so objections welcome now.
