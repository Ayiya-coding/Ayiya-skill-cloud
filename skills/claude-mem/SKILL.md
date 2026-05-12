---
name: claude-mem
description: Use local claude-mem worker HTTP APIs to search and save cross-session memory from Codex. Trigger when user asks about previous sessions, prior fixes, historical decisions, or wants to save a durable memory note.
---

# claude-mem for Codex

This is a Codex-adapted version of claude-mem memory search.

The original Claude MCP tools (`search`, `timeline`, `get_observations`) are replaced by direct HTTP API calls to the local worker (`http://127.0.0.1:37777`).

## When To Use

Use this skill when users ask questions like:

- "Did we already solve this?"
- "How did we implement X before?"
- "What changed last week?"
- "Save this as memory for later"

## Preflight (Always First)

Before memory operations, verify worker health:

```powershell
python C:\Users\85337\.codex\skills\claude-mem\scripts\claude_mem_client.py health
```

If unhealthy/unreachable, report that memory features are unavailable until worker is running.

## 3-Step Workflow (Required)

Do not fetch large details first. Always run `search -> timeline -> fetch`.

### Step 1: Search Index (cheap filtering)

```powershell
python C:\Users\85337\.codex\skills\claude-mem\scripts\claude_mem_client.py search --query "authentication" --project "my-project" --limit 20
```

Supported useful flags:

- `--query`
- `--project`
- `--type` (`observations|sessions|prompts`)
- `--obs-type` (comma-separated: `bugfix,feature,decision,discovery,change`)
- `--date-start` / `--date-end`
- `--order-by` (`date_desc|date_asc|relevance`)

### Step 2: Timeline Context (optional but recommended)

```powershell
python C:\Users\85337\.codex\skills\claude-mem\scripts\claude_mem_client.py timeline --anchor 11131 --depth-before 3 --depth-after 3 --project "my-project"
```

Or query-centered timeline:

```powershell
python C:\Users\85337\.codex\skills\claude-mem\scripts\claude_mem_client.py timeline --query "authentication" --depth-before 3 --depth-after 3 --project "my-project"
```

### Step 3: Fetch Full Records (only selected IDs)

```powershell
python C:\Users\85337\.codex\skills\claude-mem\scripts\claude_mem_client.py fetch --ids 11131,10942 --project "my-project"
```

Use a single batch fetch for multiple IDs.

## Save Memory Note

Persist a manual memory observation:

```powershell
python C:\Users\85337\.codex\skills\claude-mem\scripts\claude_mem_client.py save --text "Root cause: auth token expiry mismatch in middleware." --title "Auth expiry RCA" --project "my-project"
```

## Additional Utilities

```powershell
python C:\Users\85337\.codex\skills\claude-mem\scripts\claude_mem_client.py projects
python C:\Users\85337\.codex\skills\claude-mem\scripts\claude_mem_client.py stats
```

## Output Rules

- Keep responses concise and evidence-based.
- Cite returned observation IDs when summarizing memory.
- If no results, explicitly say no matching memory was found.
- If worker is down, state that clearly and provide the health check command.
