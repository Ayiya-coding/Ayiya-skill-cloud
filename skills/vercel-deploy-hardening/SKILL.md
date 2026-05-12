---
name: vercel-deploy-hardening
description: Use when deploying or debugging Vercel projects that show contradictory signals between browser, CLI, aliases, and runtime logs, especially false CORS, stale hashed frontend bundles after deploy, or Prisma SQLite failures that only happen on Vercel.
---

# Vercel Deploy Hardening

## Overview

This skill is a persistent field manual for the failure modes that waste the most time on Vercel: platform protection disguised as CORS, stale frontend bundles after a successful deploy, route-surface conflicts, and SQLite apps that only break on Vercel.

Use it to decide what is actually broken before changing code.

## When to Use

Use when any of these are true:

- the browser says CORS, but the network result is `401`, `404`, or HTML
- the CLI exits oddly (`spawn EPERM`, `spawn npm ENOENT`), but the deployment might still be live
- `/api/health` works but nested routes fail
- the browser still references an old hashed JS file after a new frontend deploy
- login or another DB-backed route fails only on Vercel
- backend logs do not show the request the browser claims is failing

Do not use for generic Vercel setup from scratch. Use `vercel-deploy` first.

## Triage Order

1. Verify the live aliases first.
2. Fetch the live URL through authenticated Vercel tooling before trusting a browser error.
3. Query runtime logs for the latest deployment before patching code.
4. Only after that decide whether the failure is frontend, routing, platform, or backend.

## Core Checks

### 1) Apparent CORS vs platform protection

If the response body is Vercel HTML such as `Authentication Required`, the issue is deployment protection, not app CORS.

Evidence:

- browser reports missing `Access-Control-Allow-Origin`
- response body is HTML, not app JSON
- authenticated Vercel fetch confirms Vercel HTML

Action:

- disable Vercel Deployment Protection / Vercel Authentication for public browser-facing APIs

### 2) Backend never logged the failing request

If the latest backend deployment never logged `POST /api/auth/login` or the route the browser claims is failing, do not patch the backend yet.

Suspect instead:

- stale frontend assets
- wrong frontend `baseURL`
- wrong alias or rewrite target
- browser cache

### 3) Compare asset hashes

When the console stack trace references a hashed frontend bundle:

- fetch live `/login`
- read the referenced JS hash
- compare it with the hash in the browser error

If they differ, the browser is still on an old bundle. Hard refresh or incognito is the next step, not another backend redeploy.

### 4) `/api/health` must validate the critical dependency

A static `{"status":"ok"}` health route is not a real health check.

For database-backed apps, `/api/health` should execute a minimal real query. Otherwise broken bundles, missing env, or read-only filesystem errors can look healthy until login fails.

### 5) Express route-surface conflicts

If the project framework is `express`, do not also ship `api/[...path].js` unless you intentionally want a different deployment surface.

Failure pattern:

- `/api/health` works
- flat routes work
- nested `/api/*/*` routes return Vercel `NOT_FOUND`

### 6) Prisma SQLite on Vercel

If SQLite-backed Prisma works locally but fails on Vercel:

- include the DB file with `functions.includeFiles`
- explicitly trace the Prisma asset directory from code
- copy the bundled DB into `/tmp`
- `chmod` the runtime directory and DB file
- rewrite `DATABASE_URL` to the runtime copy
- verify runtime diagnostics such as `bundledExists`, `runtimeExists`, and `writable`

If those diagnostics are not all true, the route failure is downstream of deployment packaging, not business logic.

### 7) CLI oddities on Windows

Treat these carefully:

- `spawn EPERM` after deploy/build/pull
- `spawn npm ENOENT` during local `vercel build`

Rules:

- set `NO_UPDATE_NOTIFIER=1` for scripted CLI runs
- trust alias state, fetched live URLs, and runtime logs more than the final CLI exit code
- if local build tooling is broken, let Vercel build remotely rather than blocking on local environment cleanup

## Release Gate

Do not call the deploy healthy until all of these are true:

1. the intended alias points to the intended deployment
2. frontend `/` and `/login` return `200`
3. `/login` references the expected latest bundle hash
4. `/favicon.ico` resolves
5. backend `/api/health` returns `200` and validates the critical dependency
6. at least one nested backend route returns app-level status, not Vercel `NOT_FOUND`
7. runtime logs show the request path you are debugging, if the browser claims it is reaching the backend

## Common Mistakes

- changing CORS code before ruling out Vercel protection
- debugging backend logic when backend logs never saw the request
- trusting a static health endpoint
- treating a stale frontend bundle as a failed backend deploy
- treating `spawn EPERM` as proof the deploy failed
