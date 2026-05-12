# Risk And Stability Rules

## Allowed Stability Techniques

- Use a real user-controlled Chrome profile with manual login.
- Pace actions with short jitter to avoid breaking reactive UI.
- Use default concurrency `1`; raise it only after a small successful test.
- Back off on 429, "too many requests", quota, queue, or account-risk messages.
- Stop and ask the user to handle CAPTCHA, MFA, email verification, payment confirmation, or account warnings.
- Respect site terms, robots guidance, account limits, and user permissions.

## Do Not Do

- Do not solve or outsource CAPTCHA automatically.
- Do not bypass MFA, paywalls, private data boundaries, or access controls.
- Do not spoof identities, rotate proxies/accounts, fake fingerprints, or hide automated abuse.
- Do not scrape large volumes when the site exposes an official export/API path.
- Do not continue after explicit anti-automation or account-risk warnings.

## Failure Handling

Capture these artifacts on failure when possible:

- current URL and page title
- screenshot
- body text sample
- last action and selector
- network URLs related to downloads or API calls, if already observed
- checkpoint state path

Then decide: retry the same step, resume from checkpoint, write a site-specific adapter, or ask the user for manual intervention.
