# Evidence Answering Policy

## Core Rule
Answer from captured corpus content first. Every key claim must map to at least one source URL.

## Response Pattern
1. Direct answer in plain language.
2. Evidence bullets with source URLs.
3. `Inference:` section only when needed.
4. Coverage note when content is missing.

## Missing Information
When a requested detail is absent, use this exact statement:
- `Not found in crawled pages`

Then suggest one concrete crawl update:
- expand depth
- allow cross-domain links
- include API reference path

## Risk Controls
- Do not invent endpoint names, auth schemes, limits, or status codes.
- Separate facts from assumptions.
- Keep citations visible in guides and Q&A outputs.
