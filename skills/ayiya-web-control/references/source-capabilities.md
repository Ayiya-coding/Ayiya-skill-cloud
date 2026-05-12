# Source Capabilities Extracted From Lovart Automation

The provided `lovart-image-conversation-automation` skill contributes these reusable patterns:

| Capability | Generalized Pattern |
| --- | --- |
| Persistent login | Launch a dedicated visible Chrome profile once, let the user log in manually, then reuse the profile through CDP. |
| Browser control | Start Chrome with `--remote-debugging-port`, `--user-data-dir`, fixed language/window size, and connect with Playwright `connect_over_cdp`. |
| Profile readiness | Check profile existence and cookie storage before automation; if missing, print a manual login bootstrap command and stop. |
| File upload | Try `expect_file_chooser` from the visible upload control; fall back to hidden `input[type=file]`. |
| UI stability | Close modals, press Escape, retry clicks, wait for selectors/functions, and keep concurrency low. |
| Task queue | Parse tasks, assign each a 1-based index, process a bounded range, and keep per-task status. |
| Checkpoint resume | Store completed indexes and session IDs in JSON after each success; skip completed work on rerun. |
| Failure isolation | Record single-task failures, continue to the next task, and abort after repeated global failures. |
| Risk-control detection | Stop immediately when hCaptcha/risk-control requests appear. |
| Progress reporting | Print absolute progress, elapsed time, failed items, and session previews. |
| Data extraction | Use DOM queries and stable test IDs to detect task completion and extract result URLs. |
| Local download | Download result URLs to deterministic filenames and per-category directories. |

Keep Lovart-specific selectors, prompt parsing, and demographic output folders out of the generic framework. Recreate those details only in a temporary site adapter when a target website requires them.
