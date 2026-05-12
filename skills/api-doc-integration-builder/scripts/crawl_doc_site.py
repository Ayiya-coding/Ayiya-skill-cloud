#!/usr/bin/env python3
import argparse
import json
import re
import time
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "api-doc-integration-builder/1.0"


class LinkAndTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.title_parts = []
        self.text_parts = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script", "style", "noscript"):
            self._skip_depth += 1
        if tag == "a":
            for name, value in attrs:
                if name.lower() == "href" and value:
                    self.links.append(value.strip())
                    break
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style", "noscript") and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if not data or self._skip_depth > 0:
            return
        text = re.sub(r"\s+", " ", data.strip())
        if not text:
            return
        self.text_parts.append(text)
        if self._in_title:
            self.title_parts.append(text)


def normalize_url(raw_url):
    if not raw_url:
        return ""
    clean = urldefrag(raw_url.strip())[0]
    return clean


def decode_body(raw_bytes, content_type):
    charset = None
    match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type or "", re.IGNORECASE)
    if match:
        charset = match.group(1).strip()
    for encoding in (charset, "utf-8", "utf-16", "latin-1"):
        if not encoding:
            continue
        try:
            return raw_bytes.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            pass
    return raw_bytes.decode("utf-8", errors="replace")


def is_http_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https")


def is_text_like(content_type):
    lowered = (content_type or "").lower()
    return any(
        item in lowered
        for item in (
            "text/",
            "application/json",
            "application/xml",
            "application/xhtml+xml",
            "application/javascript",
        )
    )


def fetch_url(url, timeout):
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*;q=0.8",
        },
    )
    with urlopen(req, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        content_type = response.headers.get("Content-Type", "")
        body = response.read()
    return status, content_type, decode_body(body, content_type)


def in_scope(url, root_host, allow_cross_domain, path_prefix):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if not allow_cross_domain and parsed.netloc != root_host:
        return False
    if path_prefix and not parsed.path.startswith(path_prefix):
        return False
    return True


def unique_ordered(values):
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def crawl(args):
    start_url = normalize_url(args.url)
    start_parsed = urlparse(start_url)
    if not is_http_url(start_url):
        raise ValueError("--url must be http or https")

    include_regex = re.compile(args.include_regex) if args.include_regex else None
    exclude_regex = re.compile(args.exclude_regex) if args.exclude_regex else None

    queue = deque([(start_url, 0)])
    visited = set()
    pages = []
    failures = []

    while queue and len(pages) < args.max_pages:
        current_url, depth = queue.popleft()
        if current_url in visited:
            continue
        if not in_scope(current_url, start_parsed.netloc, args.allow_cross_domain, args.path_prefix):
            continue
        if include_regex and not include_regex.search(current_url):
            continue
        if exclude_regex and exclude_regex.search(current_url):
            continue

        visited.add(current_url)
        try:
            status, content_type, body_text = fetch_url(current_url, args.timeout)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            failures.append({"url": current_url, "depth": depth, "error": str(exc)})
            continue

        links = []
        title = ""
        text = ""
        if is_text_like(content_type):
            if "html" in (content_type or "").lower():
                parser = LinkAndTextExtractor()
                parser.feed(body_text)
                title = " ".join(parser.title_parts).strip()
                text = " ".join(parser.text_parts).strip()
                for href in parser.links:
                    next_url = normalize_url(urljoin(current_url, href))
                    if not next_url or not is_http_url(next_url):
                        continue
                    if next_url.startswith("javascript:") or next_url.startswith("mailto:"):
                        continue
                    if include_regex and not include_regex.search(next_url):
                        continue
                    if exclude_regex and exclude_regex.search(next_url):
                        continue
                    if not in_scope(next_url, start_parsed.netloc, args.allow_cross_domain, args.path_prefix):
                        continue
                    links.append(next_url)
                links = unique_ordered(links)
            else:
                text = re.sub(r"\s+", " ", body_text).strip()

        pages.append(
            {
                "url": current_url,
                "depth": depth,
                "status": status,
                "content_type": content_type,
                "title": title,
                "text": text,
                "links": links,
                "fetched_at": int(time.time()),
            }
        )

        if depth < args.max_depth:
            for link in links:
                if link not in visited:
                    queue.append((link, depth + 1))

        if args.delay > 0:
            time.sleep(args.delay)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages_path = out_dir / "pages.jsonl"
    with pages_path.open("w", encoding="utf-8") as handle:
        for page in pages:
            handle.write(json.dumps(page, ensure_ascii=False) + "\n")

    failures_path = out_dir / "failures.jsonl"
    with failures_path.open("w", encoding="utf-8") as handle:
        for failure in failures:
            handle.write(json.dumps(failure, ensure_ascii=False) + "\n")

    site_map_path = out_dir / "site_map.txt"
    with site_map_path.open("w", encoding="utf-8") as handle:
        for page in pages:
            handle.write(f"{'  ' * page['depth']}- {page['url']}\n")

    report = {
        "start_url": start_url,
        "max_pages": args.max_pages,
        "max_depth": args.max_depth,
        "allow_cross_domain": args.allow_cross_domain,
        "path_prefix": args.path_prefix,
        "pages_crawled": len(pages),
        "failures": len(failures),
        "output_dir": str(out_dir),
    }
    report_path = out_dir / "crawl_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Crawled pages: {len(pages)}")
    print(f"Failed pages: {len(failures)}")
    print(f"Corpus: {pages_path}")
    print(f"Report: {report_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Crawl a docs site into a local JSONL corpus.")
    parser.add_argument("--url", required=True, help="Root URL to crawl.")
    parser.add_argument("--out", required=True, help="Output folder for crawl artifacts.")
    parser.add_argument("--max-pages", type=int, default=250, help="Maximum pages to crawl.")
    parser.add_argument("--max-depth", type=int, default=3, help="Maximum link depth from root.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout in seconds.")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between requests in seconds.")
    parser.add_argument("--allow-cross-domain", action="store_true", help="Allow crawling external domains.")
    parser.add_argument("--path-prefix", default="", help="Restrict crawl to URL path prefix, e.g. /docs.")
    parser.add_argument("--include-regex", default="", help="Only include URLs matching this regex.")
    parser.add_argument("--exclude-regex", default="", help="Skip URLs matching this regex.")
    return parser.parse_args()


def main():
    args = parse_args()
    crawl(args)


if __name__ == "__main__":
    main()
