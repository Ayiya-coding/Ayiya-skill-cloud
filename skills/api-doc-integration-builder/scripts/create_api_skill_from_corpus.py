#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def load_pages(corpus_path):
    pages = []
    with Path(corpus_path).open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            pages.append(json.loads(raw))
    return pages


def validate_skill_name(name):
    return re.fullmatch(r"[a-z0-9-]{1,63}", name or "") is not None


def slug_to_title(slug):
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def write_skill_files(skill_dir, skill_name, pages):
    source_host = ""
    if pages:
        source_host = urlparse(pages[0].get("url", "")).netloc

    description = (
        f"Answer and integrate against the crawled API documentation corpus from {source_host or 'the source docs'}, "
        "with source URL citations. Use when users ask questions about this API, request implementation guidance, "
        "or need doc-grounded integration tasks."
    )

    skill_md = "\n".join(
        [
            "---",
            f"name: {skill_name}",
            f'description: "{description}"',
            "---",
            "",
            f"# {slug_to_title(skill_name)}",
            "",
            "## Goal",
            "Answer questions and integration tasks using the captured docs corpus only.",
            "",
            "## Rules",
            "- Cite URLs from `references/source-urls.md` for key claims.",
            "- Mark assumptions as `Inference:`.",
            "- If the corpus does not contain an answer, say `Not found in crawled pages`.",
            "",
            "## Workflow",
            "1. Read `references/source-urls.md` for documentation scope.",
            "2. Use `references/key-notes.md` for high-value snippets.",
            "3. Provide answer or integration plan with citations.",
            "",
            "## References",
            "- Source URLs: `references/source-urls.md`",
            "- Key notes: `references/key-notes.md`",
            "",
        ]
    )
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    agents_yaml = "\n".join(
        [
            "interface:",
            f'  display_name: "{slug_to_title(skill_name)}"',
            '  short_description: "Answer and integrate from API docs corpus"',
            '  default_prompt: "Use this docs corpus to answer with citations and produce an integration plan for my project."',
            "",
        ]
    )
    agents_dir = skill_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "openai.yaml").write_text(agents_yaml, encoding="utf-8")

    references_dir = skill_dir / "references"
    references_dir.mkdir(parents=True, exist_ok=True)

    source_urls = ["# Source URLs", ""]
    for page in pages[:300]:
        title = page.get("title") or "(no title)"
        url = page.get("url") or ""
        source_urls.append(f"- {title}: {url}")
    source_urls.append("")
    (references_dir / "source-urls.md").write_text("\n".join(source_urls), encoding="utf-8")

    key_notes = ["# Key Notes", ""]
    for page in pages[:80]:
        title = page.get("title") or "(no title)"
        url = page.get("url") or ""
        text = re.sub(r"\s+", " ", page.get("text") or "").strip()
        if not text:
            continue
        snippet = text[:280]
        key_notes.append(f"## {title}")
        key_notes.append(f"- URL: {url}")
        key_notes.append(f"- Snippet: {snippet}")
        key_notes.append("")
    if len(key_notes) <= 2:
        key_notes.extend(["- No text snippets available in this corpus.", ""])
    (references_dir / "key-notes.md").write_text("\n".join(key_notes), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Create a new API skill scaffold from crawled corpus.")
    parser.add_argument("--corpus", required=True, help="Path to pages.jsonl from crawl_doc_site.py.")
    parser.add_argument("--skill-name", required=True, help="New skill folder name. Use lowercase letters, digits, hyphens.")
    parser.add_argument("--dest", required=True, help="Destination folder that will contain the new skill.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing skill directory.")
    return parser.parse_args()


def main():
    args = parse_args()
    if not validate_skill_name(args.skill_name):
        raise ValueError("Invalid --skill-name. Use lowercase letters, digits, and hyphens only.")

    pages = load_pages(args.corpus)
    dest_root = Path(args.dest)
    skill_dir = dest_root / args.skill_name
    if skill_dir.exists():
        if not args.force:
            raise FileExistsError(f"Target skill already exists: {skill_dir}")
    else:
        skill_dir.mkdir(parents=True, exist_ok=True)

    write_skill_files(skill_dir, args.skill_name, pages)
    print(f"Created skill at: {skill_dir}")


if __name__ == "__main__":
    main()
