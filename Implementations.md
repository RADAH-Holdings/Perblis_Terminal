## 2026-06-15 00:00 (local) - Railway MCP install for Cursor
- tag: CHORE
- area: Cursor MCP config (C:\Users\nwabu\.cursor\mcp.json)
- summary: Ran `railway mcp install --agent cursor` to register Railway's local stdio MCP server in Cursor.
- reason: User requested Railway MCP agent setup for Cursor.
- notes: Restart Cursor for the MCP server to register. Uses local CLI-backed server (`railway mcp`), not remote OAuth server.

## 2026-06-16 00:20 (local) - Railway setup agent for workspace
- tag: CHORE
- area: Railway CLI agent tooling (skills + MCP); D:\Projects\Terminal
- summary: Ran 
ailway setup agent -y from project root. Installed use-railway skill to Universal (.agents), Claude Code, Factory Droid, and Cursor; configured MCP for Claude Code and Factory Droid. Cursor MCP already present in mcp.json from prior install.
- reason: User confirmed full Railway agent tooling setup for Cursor and related editors.
- change_ref: 2026-06-15 00:00 (local) - Railway MCP install for Cursor
- notes: CLI reported already logged in (nwabueze.finance@gmail.com). Restart Cursor recommended to load skills and MCP. Cursor railway MCP: command railway, args mcp.

## 2026-06-16 (local) - Railway failed deploy log gather (resplendent-gentleness)
- tag: CHORE
- area: Railway project resplendent-gentleness; Perblis_Terminal + Worker services
- summary: Pulled build/deploy logs for latest FAILED deployments via CLI (44322e9a main, d21b1fe8 worker). Docker build succeeded; deploy failed on gunicorn `` literal and healthcheck; reported to user for manual fix.
- reason: User requested failure logs onlyùno redeploy or config changes.
- notes: Awaiting user before continuing deployment.

## 2026-06-16 01:10 (local) - Railway deploy fix (resplendent-gentleness)
- tag: FIXED
- area: backend/railway.json, backend/railway.worker.json, backend/Procfile, backend/Dockerfile, backend/settings/prod.py; Railway services Perblis_Terminal + Perblis_Terminal Worker
- summary: Fixed PORT expansion (`/bin/sh -c` + `${PORT:-8000}`), split shared vs per-service Railway config (removed startCommand/healthcheck from railway.json; set web/worker start commands via Railway environment config), added railway.worker.json, hardened Dockerfile CMD fallback, disabled SECURE_SSL_REDIRECT default for Railway internal HTTP healthchecks. Deployed web + worker via `railway up` from repo root.
- reason: Gunicorn failed with literal `$PORT`; railway.json startCommand overrode worker dashboard config; healthcheck failed on internal HTTP due to SSL redirect.
- change_ref: 2026-06-16 (local) - Railway failed deploy log gather (resplendent-gentleness)
- notes: Live https://perblisterminal-production.up.railway.app/healthz returns 200. Worker SUCCESS on db_worker. Push local changes to GitHub for durable auto-deploy; set worker service config file to `/backend/railway.worker.json` in dashboard if git-only worker deploys regress.

## 2026-06-16 04:20 (local) - Railway PostGIS wiring and deploy follow-up
- tag: CHORE
- area: Railway resplendent-gentleness; Perblis_Terminal + Worker + PostGIS; backend/railway.json, railway.worker.json, Dockerfile, Procfile, settings/prod.py
- summary: Verified PostGIS connected to web and worker via `DATABASE_URL` (`postgis://` + `postgis.railway.internal:5432`) on both services per DEPLOY.md. Production probes pass (`/healthz`, `/readyz` database ok; worker `db_worker` running). Restored web `startCommand`/`healthcheckPath` in `railway.json`; added `railway.worker.json` for worker-only start. Redeployed web from local fixes after env-var change triggered failed main-branch deploy (`$PORT` literal).
- reason: User requested Railway deployment follow-up ù DB wiring verification, endpoint tests, wave-zero check, and PR for durable git deploy.
- change_ref: 2026-06-16 01:10 (local) - Railway deploy fix (resplendent-gentleness)
- notes: Portal Cloudflare Workers deploy still pending (wave-0 exit partial). Worker `railway.worker.json` config path should be set in Railway dashboard when git auto-deploy lands. R2/Bachs integrations `not_configured` in readyz (expected).

## 2026-06-16 04:45 (local) - Git branch push for Railway deploy PR
- tag: CHORE
- area: git branch deploy/railway-wave0-followup; .gitignore
- summary: Pushed deploy fixes to `origin/deploy/railway-wave0-followup` (commits 0150715, 4a12ba3, 127386d). Removed tracked `.cursor/settings.json`; added `.cursor/` to `.gitignore`. Production redeployed SUCCESS from repo root for web + worker.
- reason: Durable git-based auto-deploy on merge to main; PR workflow per user request.
- change_ref: 2026-06-16 04:20 (local) - Railway PostGIS wiring and deploy follow-up
- notes: `gh` installed but not authenticated ó user must `gh auth login` then create PR, or open compare URL manually.
