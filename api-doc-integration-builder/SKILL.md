---
name: api-doc-integration-builder
description: "Crawl technical API documentation websites (including hyperlinks and subpages), build a local source corpus, answer questions strictly from captured pages with citations, and generate project-specific integration guides or a new API integration skill. Use when users ask to read API docs, follow linked pages, answer from docs, write integration guidance, or create an API skill from documentation."
---

# API Doc Integration Builder

## Goal
Turn one documentation URL into evidence-backed outputs:
- Crawl root page plus linked subpages into a local corpus.
- Answer questions from the captured text with source URLs.
- Generate project-specific integration guidance.
- Scaffold a dedicated API-integration skill from the same corpus.

## Quick Start
1. Crawl the docs site:
   - `python scripts/crawl_doc_site.py --url <DOC_URL> --out ./doc_runs/<name> --max-pages 250 --max-depth 3`
2. Search evidence for a question:
   - `python scripts/search_doc_corpus.py --corpus ./doc_runs/<name>/pages.jsonl --query "<QUESTION>" --top 6`
3. Build integration guidance:
   - `python scripts/build_integration_guide.py --corpus ./doc_runs/<name>/pages.jsonl --project-context "<PROJECT_NEEDS>" --out ./doc_runs/<name>/integration-guide.md`
4. Create a new API skill from the docs:
   - `python scripts/create_api_skill_from_corpus.py --corpus ./doc_runs/<name>/pages.jsonl --skill-name <new-skill-name> --dest <skills-folder>`

## Workflow
1. Confirm crawl scope: start URL, max depth, and whether cross-domain links are required.
2. Crawl the site with `scripts/crawl_doc_site.py`.
3. Validate coverage from `crawl_report.json` and `site_map.txt`.
4. Answer doc questions with `scripts/search_doc_corpus.py`.
5. Produce project-specific guide with `scripts/build_integration_guide.py`.
6. If requested, generate a reusable API skill with `scripts/create_api_skill_from_corpus.py`.

## Q&A Rules
- Use corpus text first. Avoid filling missing details with assumptions.
- Cite at least one source URL per key claim.
- Mark non-explicit conclusions as `Inference:`.
- If information is missing, state `Not found in crawled pages` and propose how to expand scope.

## Output Rules
- Keep raw crawl data and generated files in per-run folders under `doc_runs/`.
- Do not overwrite existing guides unless explicitly asked.
- Preserve evidence links in all generated guides and skill references.

## References
- Crawl strategy: `references/crawl-strategy.md`
- Evidence policy: `references/evidence-answering.md`
- Guide and skill output recipes: `references/output-recipes.md`
