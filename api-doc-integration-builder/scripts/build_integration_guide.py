#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
from pathlib import Path


def load_pages(corpus_path):
    pages = []
    with Path(corpus_path).open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            pages.append(json.loads(raw))
    return pages


def tokenize(text):
    return re.findall(r"[A-Za-z0-9_/\-]{2,}", (text or "").lower())


def score_page(page, query_terms):
    title = (page.get("title") or "").lower()
    text = (page.get("text") or "").lower()
    url = (page.get("url") or "").lower()
    score = 0.0
    for term in query_terms:
        score += text.count(term)
        score += title.count(term) * 3
        score += url.count(term) * 2
    return score


def get_top_pages(pages, query, top_n):
    terms = tokenize(query)
    if not terms:
        return pages[:top_n]
    scored = []
    for page in pages:
        score = score_page(page, terms)
        if score <= 0:
            continue
        scored.append((score, page))
    if not scored:
        return pages[:top_n]
    scored.sort(key=lambda item: -item[0])
    return [item[1] for item in scored[:top_n]]


def extract_endpoint_candidates(pages):
    method_path = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+(/[A-Za-z0-9_./{}:-]+)")
    api_path = re.compile(r"\b(/api/[A-Za-z0-9_./{}:-]+)")

    found = {}
    for page in pages:
        text = page.get("text") or ""
        url = page.get("url") or ""
        for method, path in method_path.findall(text):
            key = (method, path)
            if key not in found:
                found[key] = url
        for path in api_path.findall(text):
            key = ("ANY", path)
            if key not in found:
                found[key] = url
    endpoints = []
    for (method, path), source in found.items():
        endpoints.append({"method": method, "path": path, "source": source})
    endpoints.sort(key=lambda item: (item["method"], item["path"]))
    return endpoints


def extract_keyword_evidence(pages, keywords, limit=6):
    snippets = []
    for page in pages:
        text = page.get("text") or ""
        lowered = text.lower()
        for keyword in keywords:
            idx = lowered.find(keyword)
            if idx < 0:
                continue
            start = max(0, idx - 120)
            end = min(len(text), idx + 240)
            snippet = re.sub(r"\s+", " ", text[start:end]).strip()
            snippets.append(
                {
                    "keyword": keyword,
                    "snippet": snippet,
                    "source": page.get("url") or "",
                }
            )
            break
        if len(snippets) >= limit:
            break
    return snippets


def parse_args():
    parser = argparse.ArgumentParser(description="Generate project-specific integration guide from docs corpus.")
    parser.add_argument("--corpus", required=True, help="Path to pages.jsonl.")
    parser.add_argument("--project-context", default="", help="Free text context about target project.")
    parser.add_argument("--project-context-file", default="", help="Optional file with project context.")
    parser.add_argument("--out", required=True, help="Output markdown path.")
    parser.add_argument("--top-pages", type=int, default=12, help="How many relevant pages to use.")
    return parser.parse_args()


def load_project_context(args):
    context = args.project_context.strip()
    if args.project_context_file:
        file_text = Path(args.project_context_file).read_text(encoding="utf-8").strip()
        if context:
            context = context + "\n\n" + file_text
        else:
            context = file_text
    return context


def build_markdown(pages, top_pages, endpoints, auth_evidence, limit_evidence, error_evidence, project_context):
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# API Integration Guide")
    lines.append("")
    lines.append(f"- Generated at: {now}")
    lines.append(f"- Corpus pages loaded: {len(pages)}")
    lines.append(f"- Relevant pages used: {len(top_pages)}")
    lines.append("")
    lines.append("## Project Context")
    lines.append("")
    lines.append(project_context if project_context else "Not provided.")
    lines.append("")
    lines.append("## Source Documentation")
    lines.append("")
    for page in top_pages:
        title = page.get("title") or "(no title)"
        url = page.get("url") or ""
        lines.append(f"- {title}: {url}")
    lines.append("")
    lines.append("## Authentication Notes")
    lines.append("")
    if auth_evidence:
        for item in auth_evidence:
            lines.append(f"- `{item['keyword']}`: {item['snippet']}  (source: {item['source']})")
    else:
        lines.append("- Not found in crawled pages. Confirm auth model manually.")
    lines.append("")
    lines.append("## Endpoint Candidates")
    lines.append("")
    if endpoints:
        lines.append("| Method | Path | Source |")
        lines.append("| --- | --- | --- |")
        for item in endpoints[:40]:
            lines.append(f"| {item['method']} | `{item['path']}` | {item['source']} |")
    else:
        lines.append("- Not found in crawled pages. Expand crawl depth or include API reference pages.")
    lines.append("")
    lines.append("## Rate Limits and Quotas")
    lines.append("")
    if limit_evidence:
        for item in limit_evidence:
            lines.append(f"- `{item['keyword']}`: {item['snippet']}  (source: {item['source']})")
    else:
        lines.append("- Not found in crawled pages.")
    lines.append("")
    lines.append("## Error Handling")
    lines.append("")
    if error_evidence:
        for item in error_evidence:
            lines.append(f"- `{item['keyword']}`: {item['snippet']}  (source: {item['source']})")
    else:
        lines.append("- Not found in crawled pages.")
    lines.append("")
    lines.append("## Implementation Plan")
    lines.append("")
    lines.append("1. Confirm environments, base URL, auth credentials, and required scopes.")
    lines.append("2. Implement authentication and token refresh flow first.")
    lines.append("3. Integrate core read/write endpoints with request and response schemas.")
    lines.append("4. Add retry, timeout, rate-limit backoff, and idempotency controls.")
    lines.append("5. Add logging, monitoring, and contract tests against documented behavior.")
    lines.append("")
    lines.append("## Open Questions")
    lines.append("")
    if not auth_evidence:
        lines.append("- Auth mechanism and token lifecycle are not explicit in current corpus.")
    if not endpoints:
        lines.append("- Endpoint list is incomplete or hidden in uncrawled pages.")
    if not limit_evidence:
        lines.append("- Rate limit policy is missing; verify before production rollout.")
    if not error_evidence:
        lines.append("- Error schema/examples are missing; define fallback parsing strategy.")
    if auth_evidence and endpoints and limit_evidence and error_evidence:
        lines.append("- No major coverage gaps detected in sampled pages.")
    lines.append("")
    lines.append("## Verification Checklist")
    lines.append("")
    lines.append("- [ ] Auth flow tested with invalid and expired credentials.")
    lines.append("- [ ] Endpoint happy path and failure path both tested.")
    lines.append("- [ ] Retries and backoff behavior validated under throttling.")
    lines.append("- [ ] Request/response logs include trace IDs and redaction rules.")
    lines.append("- [ ] All key claims in this guide can be traced to source URLs.")
    lines.append("")
    return "\n".join(lines)


def main():
    args = parse_args()
    pages = load_pages(args.corpus)
    project_context = load_project_context(args)
    query = " ".join(
        [
            project_context,
            "authentication authorization token api key endpoint request response status code rate limit error webhook sdk",
        ]
    ).strip()
    top_pages = get_top_pages(pages, query, args.top_pages)
    endpoints = extract_endpoint_candidates(top_pages)
    auth_evidence = extract_keyword_evidence(
        top_pages, ["oauth", "auth", "token", "api key", "apikey", "bearer", "jwt", "signature", "hmac"]
    )
    limit_evidence = extract_keyword_evidence(top_pages, ["rate limit", "quota", "throttle", "429", "burst"])
    error_evidence = extract_keyword_evidence(
        top_pages, ["error", "status code", "retry", "timeout", "failure", "exception", "4xx", "5xx"]
    )

    output = build_markdown(
        pages=pages,
        top_pages=top_pages,
        endpoints=endpoints,
        auth_evidence=auth_evidence,
        limit_evidence=limit_evidence,
        error_evidence=error_evidence,
        project_context=project_context,
    )
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output + "\n", encoding="utf-8")
    print(f"Wrote integration guide: {output_path}")


if __name__ == "__main__":
    main()
