---
name: vercel-deploy
description: Use when the user wants a Vercel deployment created, promoted, verified, or debugged, especially for preview or production releases on split frontend/backend projects, browser-facing APIs, or Vercel-hosted Prisma SQLite apps.
---

# Vercel Deploy

Deploy projects to Vercel with a bias toward preview deploys first. Only deploy to production when the user explicitly asks, or when promoting a preview the user already approved.

For contradictory real-world signals such as false CORS, stale hashed frontend assets, or SQLite failures that only appear on Vercel, also use `vercel-deploy-hardening`.

## Preflight

- Run from the actual project directory that should be linked to Vercel.
- Prefer the project-local CLI when available (`node_modules/vercel/dist/vc.js`) if `vercel` is not on PATH.
- Set `NO_UPDATE_NOTIFIER=1` for scripted CLI runs on Windows to reduce noisy trailing update-check failures.
- If the CLI says credentials are missing or invalid, run `vercel login` and complete the device flow before retrying.
- If local build or inspect commands say project settings are missing, run `vercel pull --yes --environment <preview|production>` first.
- On Windows or sandboxed environments, treat trailing `spawn EPERM` carefully: it can be a CLI update-check or local build-helper failure after a successful deploy/build/pull. Verify side effects before declaring failure.

## Default Commands

Preview deploy:

```bash
vercel deploy -y
```

Production deploy:

```bash
vercel deploy --prod -y
```

If the global CLI is unavailable but the dependency is installed locally:

```bash
node ./node_modules/vercel/dist/vc.js deploy -y
node ./node_modules/vercel/dist/vc.js deploy --prod -y
```

Use a long timeout for deploy/build commands. Ten minutes is reasonable.

## Verification After Deploy

Do not stop at the deployment URL. Verify the deployed behavior that commonly regresses:

1. Confirm the project's latest deployment and aliases point at the deployment you just created.
2. For SPAs, fetch `/` and at least one deep link such as `/login` and confirm they return `index.html`, not `404`.
3. Confirm `/favicon.ico` resolves cleanly; missing favicon requests are easy to overlook and create noisy false alarms.
4. For split frontend/backend setups, probe `/api/health` and at least one nested API path such as `/api/messages/friends` or `/api/sync/status`.
5. Distinguish app-level auth (`401` JSON from your app) from platform-level failure (`401` Vercel auth page, `404 NOT_FOUND`, or missing app headers).
6. For database-backed apps, make sure `/api/health` touches the database or another critical dependency. A static `{"status":"ok"}` health route is not enough.
7. If the browser console points at a hashed asset file, compare that hash with the one referenced by the live `/login` HTML. If they differ, the browser is still running an old bundle.

When the Vercel plugin is available, prefer project/deployment metadata plus authenticated fetches (`web_fetch_vercel_url`) over guessing from the CLI exit code alone.

## Split Frontend/Backend Baseline

Prefer this default for public browser-facing apps deployed as separate Vercel projects:

- frontend uses same-origin `/api` in production
- frontend `vercel.json` rewrites `/api/(.*)` to the backend production domain
- frontend `vercel.json` also rewrites `/(.*)` to `/index.html` for SPA deep links
- put the `/api/(.*)` rewrite before the SPA catch-all
- provide a real favicon asset (`/favicon.ico` or `/favicon.svg`) or rewrite `/favicon.ico` to an existing icon

If the rewrite layer becomes ambiguous during debugging, a host-aware production `baseURL` that points directly at the backend production alias is an acceptable fallback. Keep the `/api` rewrite anyway so direct probes like `/api/health` still behave predictably.

## Express Projects on Vercel

If the Vercel project framework is `express`, let the framework adapter own the deployment surface.

Do not add a manual `api/[...path].js` catch-all unless you are intentionally bypassing Vercel's Express framework handling. Mixing both can create multiple Node functions and lead to confusing behavior where:

- `/api/health` works
- flat routes work
- nested routes such as `/api/messages/friends` or `/api/sync/status` return Vercel `NOT_FOUND`

An Express deployment should behave like one app surface, not a mix of framework auto-detection plus extra catch-all functions.

## Prisma SQLite on Vercel

Prisma with SQLite requires extra care on Vercel:

- deployment files are read-only
- SQLite needs a writable file for locks and journals
- the database file may not be bundled unless it is explicitly traced

Use this pattern:

1. include the SQLite file in `vercel.json` `functions.includeFiles`
2. explicitly trace the Prisma asset directory from application code
3. on startup, copy the bundled database into `/tmp`
4. `chmod` the runtime directory and database file so SQLite can write
5. rewrite `DATABASE_URL` to point at the runtime copy
6. verify with runtime logs that the bundled file exists and the runtime copy is writable

If production login fails with `PrismaClientInitializationError` or `Unable to open the database file`, verify bundling and runtime writeability before touching auth code.

## Apparent CORS vs Vercel Protection

If the browser reports CORS but the response is actually a Vercel `401 Authentication Required` page, the root cause is deployment protection, not app CORS.

Indicators:

- response body is HTML from Vercel, not your app JSON
- browser reports missing `Access-Control-Allow-Origin`
- direct `.vercel.app` API fetch returns Vercel auth content

Fix:

- for public browser-facing APIs, disable Vercel Deployment Protection / Vercel Authentication on the production backend project
- while debugging protected deployments, use authenticated Vercel tooling such as `web_fetch_vercel_url` or a temporary access URL instead of unauthenticated browser fetches

## Windows and Automation Notes

Observed failure modes and how to handle them:

- `No project settings found locally`
  - Run `vercel pull --yes --environment <env>`.
- `specified token is not valid`
  - Re-run `vercel login` or refresh `VERCEL_TOKEN`.
- `spawn npm ENOENT` during `vercel build`
  - local `npm` is not on PATH. Fix PATH, run the build tool entrypoint directly with `node`, or skip local prebuild and use remote build/deploy.
- `spawn EPERM` after deploy/build/pull has already emitted a deployment URL, alias, or downloaded settings
  - treat as non-fatal until verification proves otherwise.
- local `curl`, PowerShell, or Node HTTP clients time out against `.vercel.app` while fetched URLs from the Vercel plugin succeed
  - prefer authenticated Vercel fetches and runtime logs over local network probing when deciding whether production is actually healthy.

## Release Gate

Do not report the deploy as complete until these pass:

1. alias points to the intended deployment
2. frontend root and deep-link routes return `200`
3. backend `/api/health` returns `200`
4. if the app depends on a database, `/api/health` proves database access
5. at least one nested backend route returns app-level status (`200`, `401`, `403`, etc.), not Vercel edge `NOT_FOUND`
6. public browser-facing APIs are not blocked by Vercel protection
7. the live HTML references the expected latest frontend asset hash when debugging browser-reported regressions
