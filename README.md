# Terminal

Map-first B2B marketplace for hiring heavy assets in Nigeria — Plant & Machinery, Trucks & Haulage, Warehousing, Terminals & Container Yards, Land & Staging.

## Repository layout

```
backend/          Django API (Wave 0 → build)
portal/           Supplier Portal — Next.js on Cloudflare Workers (Wave 0 → build)
app/              Hirer mobile app — Expo React Native (Wave 2 → build)
packages/tokens/  Shared design tokens (Wave 0 → build)
docs/             Specifications and decisions
  v2/             Current canonical specs (FSD v2.1, TSD v2.1, Design System, UX)
  legacy-v1/      Historical v1 documents — reference only
scripts/          Dev tooling
```

## Start here

| If you are... | Read first |
|---|---|
| A coding agent | [design.md](design.md) — engineering guide, commandments, conventions, wave gating |
| Reviewing product behaviour | [docs/v2/06_FSD_v2.md](docs/v2/06_FSD_v2.md) or [PDF](docs/v2/pdf/Terminal_FSD_v2.1.pdf) |
| Reviewing the technical design | [docs/v2/07_TSD.md](docs/v2/07_TSD.md) or [PDF](docs/v2/pdf/Terminal_TSD_v2.1.pdf) |
| Checking a founder decision | [docs/v2/DECISIONS.md](docs/v2/DECISIONS.md) |

## Dev quickstart

```bash
docker compose up -d                        # PostGIS + Mailpit
cd backend && uv sync
./manage.py migrate && ./manage.py runserver
# Portal: cd portal && pnpm i && pnpm dev
# App:    cd app    && pnpm i && npx expo start
```

> Build waves are gated on founder approval. See `design.md §7` and `docs/v2/07_TSD.md §10`.
