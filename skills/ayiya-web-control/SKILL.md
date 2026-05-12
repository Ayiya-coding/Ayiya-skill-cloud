---
name: ayiya-web-control
description: >
  Use when Codex needs to automate browser or website workflows: browser
  control, login with a persistent Chrome profile, form entry, clicking, file
  upload, task execution, webpage data extraction, local downloads, checkpoint
  resume, stable long-running web jobs, Playwright CDP, site-specific adapters,
  or Chinese requests such as 浏览器控制/网页自动化/登录/输入/下载/断点续跑.
---

# AyIYA Web Control

## Core Rule

Use a dedicated Chrome profile plus Playwright CDP first. Preserve the user's login session, write checkpoints after every meaningful step, and stop for human help when a site shows CAPTCHA, rate limiting, login expiry, account risk warnings, or other risk-control gates.

This skill is for authorized user-driven automation. Do not bypass CAPTCHA, defeat bot detection, rotate identities, scrape behind access controls without permission, or hide abusive automation. Human-like pacing is for UI stability and lower load, not evasion.

## Workflow

1. Confirm the target site, user goal, required inputs, output format, and whether the user can complete login manually if needed.
2. Run `scripts/ayiya_web_control.py doctor` to verify Chrome and Playwright.
3. Create or reuse a site profile under `C:\temp\ayiya-web-control\<site-key>\profile`.
4. If login is needed, run `launch-login`, let the user log in in Chrome, then reuse that profile for all future runs.
5. Recon the site with `inspect`: collect title, URL, body text sample, buttons, links, forms, and stable selectors.
6. For simple flows, write a JSON plan and run `run-plan` with checkpoint resume.
7. For complex flows, write a temporary site adapter in the user's workspace. Follow `references/site-adapter-pattern.md`.
8. Save outputs and downloads to an explicit local folder. Verify file existence, size, and expected content.

## Commands

Use the bundled helper with the current Python runtime:

```powershell
python "C:\Users\Administrator\.codex\skills\ayiya-web-control\scripts\ayiya_web_control.py" doctor
```

Manual login bootstrap:

```powershell
python "C:\Users\Administrator\.codex\skills\ayiya-web-control\scripts\ayiya_web_control.py" launch-login `
  --site-key example `
  --url "https://example.com"
```

Recon a logged-in page:

```powershell
python "C:\Users\Administrator\.codex\skills\ayiya-web-control\scripts\ayiya_web_control.py" inspect `
  --site-key example `
  --url "https://example.com/dashboard" `
  --output ".\example.inspect.json" `
  --screenshot ".\example.png"
```

Run a resumable simple plan:

```powershell
python "C:\Users\Administrator\.codex\skills\ayiya-web-control\scripts\ayiya_web_control.py" run-plan `
  --site-key example `
  --plan ".\example.plan.json" `
  --state ".\example.state.json" `
  --download-dir ".\downloads"
```

## Simple Plan Actions

`run-plan` supports these actions: `goto`, `click`, `fill`, `type`, `press`, `upload`, `wait_for_selector`, `wait_for_url`, `download_click`, `extract_text`, `extract_attr`, `screenshot`, `scroll`, and `sleep`.

Each step needs a stable `id`. Checkpoint state stores completed step IDs and extracted values, so rerunning the same command skips completed steps.

```json
[
  {"id": "open", "action": "goto", "url": "https://example.com/app"},
  {"id": "search", "action": "fill", "selector": "input[name='q']", "value": "invoice"},
  {"id": "submit", "action": "press", "selector": "input[name='q']", "key": "Enter"},
  {"id": "ready", "action": "wait_for_selector", "selector": ".result"},
  {"id": "items", "action": "extract_text", "selector": ".result", "save_as": "results"}
]
```

## Site Adapters

When a website has dynamic queues, multi-step workflows, unusual downloads, rate limits, or fragile selectors, create a site adapter instead of stretching JSON plans. Keep adapters task-specific and store them near the user's work files, not inside this skill unless the pattern becomes reusable.

Adapters should define:

- login/profile readiness checks
- selectors and readiness probes
- task normalization and idempotency keys
- submit, poll, data extraction, and download functions
- checkpoint schema with completed, failed, attempts, output paths, and session URLs
- stop conditions for CAPTCHA, 429, account warnings, or repeated failures

Load `references/site-adapter-pattern.md` before writing an adapter.

## Stability Defaults

- Default concurrency: `1`.
- Use explicit waits for DOM state, network state, or business state; avoid blind sleeps except short pacing.
- Type with small randomized delays only when the site reacts poorly to direct `fill`.
- Prefer role, label, text, `data-testid`, and semantic selectors over brittle CSS paths.
- Close transient modals and press Escape before retries.
- Retry individual steps with bounded attempts; abort after repeated global failures.
- Save checkpoints after every completed task or downloaded file.
- Capture screenshots and page text on failure.
- Stop for manual handling on CAPTCHA, hCaptcha, reCAPTCHA, Cloudflare challenges, 429/rate-limit messages, login expiry, or account-risk prompts.

## References

- `references/source-capabilities.md`: what was extracted from the Lovart automation skill.
- `references/site-adapter-pattern.md`: adapter contract and implementation checklist.
- `references/risk-and-stability.md`: safe pacing, checkpoint, and risk-control handling rules.
