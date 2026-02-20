---
name: oneclick-repo-packager
description: "Create one-click runnable bundles for GitHub/open-source projects: add Windows/macOS run scripts and a browser-based WebUI launcher. Use for requests like '???', '????', '???????', '???', or 'WebUI ??'."
---

# One-Click Repo Packager

## Goal
Create a minimal, additive launcher bundle so beginners can run a repo on Windows/macOS with one script and a WebUI.

## Workflow
1. Locate repo root and detect stack (see references/stack-detection.md).
2. Derive install and run commands from README and project files.
3. Choose WebUI approach:
   - If the project already exposes a web UI or server, use the launcher to start it and link to its URL.
   - If it is CLI-only, wrap the run command with the included WebUI launcher to provide Start/Stop and logs.
4. Add the bundle:
   - Copy `assets/script-templates/run.ps1` and `run.sh` to repo root as `run.ps1` and `run.sh`.
   - Copy `assets/webui-launcher` to `<repo>/webui`.
   - Edit `webui/config.json` with `install_cmd`, `run_cmd`, `app_url`, and `working_dir`.
5. Smoke test on Windows or macOS:
   - Run `run.ps1` (Windows) or `run.sh` (macOS).
   - Confirm the WebUI opens and can start the app.
6. Summarize how to use it for the user.

## Ask Only If Needed
- Which OSes must be supported (Windows, macOS)?
- Preferred package manager (npm/pnpm/yarn, pip/poetry)?
- Is Docker acceptable if local setup is complex?

## Output Expectations
- Additive changes only (do not refactor app code).
- Keep scripts at repo root and WebUI under `webui/`.
- Use ASCII for scripts and configs.

## References
- Stack detection: `references/stack-detection.md`
- Command matrix: `references/run-command-matrix.md`
- WebUI launcher setup: `references/webui-launcher.md`
