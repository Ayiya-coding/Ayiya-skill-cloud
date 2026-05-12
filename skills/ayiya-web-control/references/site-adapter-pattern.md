# Site Adapter Pattern

Use a site adapter when a generic JSON plan is not enough.

## Adapter Contract

Create one Python file in the user's workspace, for example:

```text
adapters/<site_key>_adapter.py
```

Recommended functions:

```python
def load_tasks(args) -> list[dict]: ...
def task_key(task: dict) -> str: ...
def ensure_ready(page, args) -> None: ...
def submit_task(page, task: dict, args) -> dict: ...
def poll_task(page, submitted: dict, args) -> dict: ...
def extract_data(page, submitted: dict, args) -> dict: ...
def download_outputs(page, submitted: dict, args) -> list[str]: ...
def detect_risk_control(page) -> str | None: ...
```

Return dictionaries with stable IDs, session URLs, status, extracted values, and local output paths.

## Checkpoint Schema

Use a JSON state file shaped like:

```json
{
  "site_key": "example",
  "profile_dir": "C:/temp/ayiya-web-control/example/profile",
  "completed": {
    "task-001": {
      "status": "complete",
      "session_url": "https://example.com/jobs/123",
      "outputs": ["C:/work/downloads/task-001.csv"]
    }
  },
  "failed": {
    "task-002": {
      "status": "timed_out",
      "attempts": 2,
      "last_error": "completion marker not found"
    }
  }
}
```

Save after every completed task and every downloaded file.

## Implementation Checklist

1. Run `doctor`, then `launch-login` if login is required.
2. Use `inspect` to capture selectors and visible text.
3. Identify robust readiness probes: URL pattern, role/label, `data-testid`, visible text, or network response.
4. Build the smallest adapter for the current user task.
5. Start with one item in headed mode and save a screenshot.
6. Add checkpoint resume before running the full batch.
7. Add bounded retries, low concurrency, and stop conditions.
8. Verify downloaded files and extracted data before reporting completion.

## Selector Guidance

Prefer:

- `page.get_by_role(...)`
- `page.get_by_label(...)`
- `page.get_by_text(...)` with exact or scoped text
- `[data-testid=...]` or durable IDs
- selectors scoped under a stable container

Avoid:

- long generated class chains
- nth-child paths unless no alternative exists
- clicking coordinates except as a last resort
- assuming text is ready before the app has finished rendering
