# Crawl Strategy

## Purpose
Capture all useful text from a technical docs site, including linked subpages, into a local corpus.

## Recommended Defaults
- `--max-depth 3`
- `--max-pages 250`
- Same host only (default)

## Scope Controls
- Use `--path-prefix /docs` when docs and marketing pages share one domain.
- Use `--include-regex` to keep only API reference pages.
- Use `--exclude-regex` for changelog/blog/login/terms pages.

## Coverage Checks
- Review `crawl_report.json` for page count and failures.
- Review `site_map.txt` for missing branches.
- If important pages are missing, increase depth or adjust include/exclude patterns.

## JS-Rendered Docs
Some docs hide content behind client-side rendering. If key pages look empty, use a browser-based capture path and merge those pages into the same `pages.jsonl`.
