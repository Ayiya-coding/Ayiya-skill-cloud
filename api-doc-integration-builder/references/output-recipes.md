# Output Recipes

## A) Q&A From Docs
1. Run `search_doc_corpus.py` with the user question.
2. Use top hits to build answer.
3. Add URL citations for each key claim.

## B) Project Integration Guide
1. Gather project goals, stack, and constraints.
2. Run `build_integration_guide.py`.
3. Validate auth, endpoint, and rate-limit coverage.
4. Add open questions for missing details.

## C) New API Skill From Docs
1. Run `create_api_skill_from_corpus.py`.
2. Confirm generated `SKILL.md` description and trigger wording.
3. Verify references include source URLs and snippets.
4. Run `quick_validate.py` on the new generated skill if available.
