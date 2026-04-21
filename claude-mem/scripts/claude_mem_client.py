#!/usr/bin/env python3
"""Minimal CLI client for local claude-mem worker APIs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_BASE_URL = os.environ.get("CLAUDE_MEM_BASE_URL", "http://127.0.0.1:37777")


def _clean_query(params: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        cleaned[key] = value
    return cleaned


def _request(
    method: str,
    path: str,
    *,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 20,
) -> Any:
    url = base_url.rstrip("/") + path
    if query:
        encoded = urllib.parse.urlencode(_clean_query(query), doseq=True)
        if encoded:
            url = f"{url}?{encoded}"

    headers = {"Accept": "application/json"}
    payload: bytes | None = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url=url, data=payload, method=method.upper(), headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        err_text = exc.read().decode("utf-8", errors="replace")
        sys.stderr.write(f"HTTP {exc.code} for {method} {path}\n{err_text}\n")
        raise SystemExit(2) from exc
    except urllib.error.URLError as exc:
        sys.stderr.write(f"Connection error for {method} {path}: {exc.reason}\n")
        raise SystemExit(2) from exc

    if "application/json" in content_type:
        return json.loads(raw.decode("utf-8"))
    return raw.decode("utf-8", errors="replace")


def _print_output(data: Any) -> None:
    if isinstance(data, (dict, list)):
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data)


def _parse_ids(ids_text: str) -> list[int]:
    ids: list[int] = []
    for part in ids_text.split(","):
        token = part.strip()
        if not token:
            continue
        ids.append(int(token))
    if not ids:
        raise ValueError("ids list is empty")
    return ids


def cmd_health(args: argparse.Namespace) -> int:
    data = _request("GET", "/api/health", base_url=args.base_url, timeout=args.timeout)
    _print_output(data)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    query = {
        "query": args.query,
        "limit": args.limit,
        "project": args.project,
        "type": args.type,
        "obs_type": args.obs_type,
        "dateStart": args.date_start,
        "dateEnd": args.date_end,
        "offset": args.offset,
        "orderBy": args.order_by,
        "format": args.format,
    }
    data = _request("GET", "/api/search", query=query, base_url=args.base_url, timeout=args.timeout)
    _print_output(data)
    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    if not args.anchor and not args.query:
        sys.stderr.write("timeline requires --anchor or --query\n")
        return 2
    if args.anchor and args.query:
        sys.stderr.write("timeline accepts either --anchor or --query, not both\n")
        return 2

    query = {
        "anchor": args.anchor,
        "query": args.query,
        "depth_before": args.depth_before,
        "depth_after": args.depth_after,
        "project": args.project,
    }
    data = _request("GET", "/api/timeline", query=query, base_url=args.base_url, timeout=args.timeout)
    _print_output(data)
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    try:
        ids = _parse_ids(args.ids)
    except ValueError as exc:
        sys.stderr.write(f"invalid --ids value: {exc}\n")
        return 2

    body = {
        "ids": ids,
        "orderBy": args.order_by,
        "limit": args.limit,
        "project": args.project,
    }
    data = _request("POST", "/api/observations/batch", body=body, base_url=args.base_url, timeout=args.timeout)
    _print_output(data)
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    body = {
        "text": args.text,
        "title": args.title,
        "project": args.project,
    }
    data = _request("POST", "/api/memory/save", body=body, base_url=args.base_url, timeout=args.timeout)
    _print_output(data)
    return 0


def cmd_projects(args: argparse.Namespace) -> int:
    data = _request("GET", "/api/projects", base_url=args.base_url, timeout=args.timeout)
    _print_output(data)
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    data = _request("GET", "/api/stats", base_url=args.base_url, timeout=args.timeout)
    _print_output(data)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI for local claude-mem worker APIs")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Worker base URL")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds")

    sub = parser.add_subparsers(dest="command", required=True)

    p_health = sub.add_parser("health", help="Check worker health")
    p_health.set_defaults(func=cmd_health)

    p_search = sub.add_parser("search", help="Search memory index")
    p_search.add_argument("--query", help="Search query text")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--project")
    p_search.add_argument("--type", choices=["observations", "sessions", "prompts"])
    p_search.add_argument("--obs-type", help="Comma-separated observation types")
    p_search.add_argument("--date-start", help="YYYY-MM-DD or epoch ms")
    p_search.add_argument("--date-end", help="YYYY-MM-DD or epoch ms")
    p_search.add_argument("--offset", type=int)
    p_search.add_argument("--order-by", choices=["date_desc", "date_asc", "relevance"])
    p_search.add_argument("--format", default="json", choices=["json", "table"])
    p_search.set_defaults(func=cmd_search)

    p_timeline = sub.add_parser("timeline", help="Get timeline around anchor or query")
    p_timeline.add_argument("--anchor", help="Observation ID, session ID (S123), or timestamp")
    p_timeline.add_argument("--query", help="Query to find anchor")
    p_timeline.add_argument("--depth-before", type=int, default=5)
    p_timeline.add_argument("--depth-after", type=int, default=5)
    p_timeline.add_argument("--project")
    p_timeline.set_defaults(func=cmd_timeline)

    p_fetch = sub.add_parser("fetch", help="Fetch full observations by IDs")
    p_fetch.add_argument("--ids", required=True, help="Comma-separated observation IDs")
    p_fetch.add_argument("--order-by", default="date_desc", choices=["date_desc", "date_asc"])
    p_fetch.add_argument("--limit", type=int)
    p_fetch.add_argument("--project")
    p_fetch.set_defaults(func=cmd_fetch)

    p_save = sub.add_parser("save", help="Save manual memory note")
    p_save.add_argument("--text", required=True, help="Memory text")
    p_save.add_argument("--title", help="Optional short title")
    p_save.add_argument("--project", help="Project name")
    p_save.set_defaults(func=cmd_save)

    p_projects = sub.add_parser("projects", help="List known projects")
    p_projects.set_defaults(func=cmd_projects)

    p_stats = sub.add_parser("stats", help="Get worker/database stats")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
