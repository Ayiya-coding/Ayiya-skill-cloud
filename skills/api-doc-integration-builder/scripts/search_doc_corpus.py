#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


def load_pages(corpus_path):
    pages = []
    path = Path(corpus_path)
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            pages.append(json.loads(raw))
    return pages


def tokenize(text):
    return re.findall(r"[A-Za-z0-9_/\-]{2,}", (text or "").lower())


def score_page(page, query, query_terms):
    title = (page.get("title") or "").lower()
    text = (page.get("text") or "").lower()
    url = (page.get("url") or "").lower()

    score = 0.0
    coverage = 0
    for term in query_terms:
        term_hits = text.count(term)
        title_hits = title.count(term)
        url_hits = url.count(term)
        if term_hits or title_hits or url_hits:
            coverage += 1
        score += term_hits
        score += title_hits * 3
        score += url_hits * 2

    if query and query in text:
        score += 20
    if query and query in title:
        score += 30
    if query_terms:
        score += (coverage / len(query_terms)) * 10
    return score


def make_snippet(text, query_terms, width=320):
    if not text:
        return ""
    lowered = text.lower()
    index = -1
    for term in query_terms:
        position = lowered.find(term)
        if position >= 0:
            index = position
            break
    if index < 0:
        snippet = text[:width]
    else:
        start = max(0, index - width // 3)
        end = min(len(text), index + width)
        snippet = text[start:end]
    return re.sub(r"\s+", " ", snippet).strip()


def search_pages(pages, query, top_n):
    lowered_query = (query or "").lower().strip()
    query_terms = tokenize(lowered_query)
    if lowered_query and not query_terms:
        query_terms = [lowered_query]

    results = []
    for page in pages:
        score = score_page(page, lowered_query, query_terms)
        if score <= 0:
            continue
        result = {
            "score": round(score, 3),
            "title": page.get("title") or "",
            "url": page.get("url") or "",
            "snippet": make_snippet(page.get("text") or "", query_terms),
            "depth": page.get("depth", 0),
        }
        results.append(result)

    results.sort(key=lambda item: (-item["score"], item["depth"], item["url"]))
    return results[:top_n]


def parse_args():
    parser = argparse.ArgumentParser(description="Search a docs corpus JSONL by keyword scoring.")
    parser.add_argument("--corpus", required=True, help="Path to pages.jsonl.")
    parser.add_argument("--query", required=True, help="Search query.")
    parser.add_argument("--top", type=int, default=6, help="Number of results.")
    parser.add_argument("--json", action="store_true", help="Output JSON only.")
    return parser.parse_args()


def main():
    args = parse_args()
    pages = load_pages(args.corpus)
    results = search_pages(pages, args.query, args.top)

    if args.json:
        print(json.dumps({"query": args.query, "results": results}, ensure_ascii=False, indent=2))
        return

    print(f"Query: {args.query}")
    print(f"Matches: {len(results)}")
    for idx, result in enumerate(results, start=1):
        title = result["title"] or "(no title)"
        print(f"{idx}. score={result['score']} title={title}")
        print(f"   url: {result['url']}")
        if result["snippet"]:
            print(f"   snippet: {result['snippet']}")


if __name__ == "__main__":
    main()
