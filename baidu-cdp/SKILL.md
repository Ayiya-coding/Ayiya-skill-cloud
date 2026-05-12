---
name: baidu-cdp
description: Capture, implement, or debug Baidu hot-search crawling through ShadowBot Browser CDP for the media-coding project. Use when Codex needs to open Baidu 热搜榜, collect ranks, titles, heat indexes, search-result/article content, Baidu-visible comments, AI summaries under 800 Chinese characters, or store Baidu hotspot/comment data in the database.
---

# Baidu CDP

## Core Rule

Treat the user-visible Baidu hot-search board and Baidu search result page as the evidence source. Do not replace a hot-search topic with unrelated third-party trending feeds or generic search API guesses.

Use this pipeline:

1. Open `https://top.baidu.com/board?tab=realtime` in ShadowBot Browser through CDP. Use `https://top.baidu.com/board` or `?tab=homepage` only as degraded fallbacks because they expose the homepage card rather than the full realtime board.
2. Parse the 热搜榜 rows exactly as shown:
   - rank
   - title
   - heat index / heat text
   - badges such as `热`, `新`, `爆`
   - board URL and topic search URL
3. For each topic, open the Baidu search URL generated from the board link or `https://www.baidu.com/s?wd=<title>`.
4. Capture the main result area:
   - Baidu answer/news card text
   - top organic/news results
   - source, publish time, snippet, resolved article URL
   - Baidu-visible interaction/comment module when present
5. Open the most relevant main article/result URL when accessible and extract readable article text. Prefer the top Baidu news/answer result that clearly explains the hot topic; do not summarize unrelated SEO pages.
6. Use AI to summarize the topic and main article evidence in no more than 800 Chinese characters.
7. Capture all comments that Baidu or the opened article exposes through visible DOM or authenticated network responses. Continue pagination/scrolling until no new comments appear, then record the real sampled count and whether the source appeared exhausted.
8. Upsert the hotspot row and replace that hotspot's comment rows in the database.
9. When a run reveals a new blocker or selector change, update this skill or its reference file before finishing the task.

## ShadowBot Runtime

Prefer the machine's ShadowBot Browser so Baidu sees the same browser state the user can inspect:

- Default executable: `D:\Program Files (x86)\ShadowBot\ShadowBot Browser\Application\ShadowBotBrowser.exe`
- Default profile: `%LOCALAPPDATA%\ShadowBotBrowser\User Data`
- Override environment variables: `SHADOWBOT_BROWSER_EXE`, `SHADOWBOT_USER_DATA_DIR`

Copy only minimal profile files into a temporary runtime profile before launching with `--remote-debugging-port=<open-port>`. Do not lock or mutate the user's real profile directly.

Never print or store cookie values. It is safe to record cookie names, counts, login presence, and whether Baidu asked for verification.

If Baidu asks for login, CAPTCHA, SMS, slider verification, or abnormal traffic verification, stop and request human intervention. After the user completes the challenge in ShadowBot, retry using the same browser login state.

## media-coding Contract

For `D:\media-coding`, implement or maintain:

- Script: `src/server/scripts/scrape-baidu-hotsearch.ts`
- Command: `npm run scrape:baidu-hotsearch`
- Platform value: `baidu`
- Optional filters:
  - `BAIDU_HOT_LIMIT=30` for normal partial runs; use `51` for the full realtime board
  - `BAIDU_TOPIC_FILTER="标题1|标题2"` for targeted refills
  - `BAIDU_COMMENT_LIMIT=0` means keep collecting until source exhaustion; otherwise cap for smoke tests
  - `BAIDU_AI_ANALYZER=codex|claude|none` (`codex` is the intended default; use `none` for smoke tests)
  - `BAIDU_KEEP_PROFILE=1` only while debugging
- API verification:
  - `GET http://127.0.0.1:8787/api/hotspots?platform=baidu&status=active&limit=100&sort=rank&direction=asc&include_raw=true`

Expected `hotspots.raw_payload` shape:

- `capture`: captured_at, source, board_url, login_state, selectors_version, failures
- `board_item`: rank, title, heat_index, heat_text, badges, board_link, search_url
- `search_page`: url, baidu_answer, main_results, visible_comments, related_hotspots
- `main_article`: title, source, published_at, url, resolved_url, text_excerpt, extraction_status
- `ai_summary`: summary, analyzer, input_sources, character_count, limitations
- `top_comments`: all collected comments or the full bounded sample when the platform gates pagination
- `comment_fetch`: requested_limit, collected, exhausted, sources, failures

Store comments both in the `comments` table and in `raw_payload.top_comments`, because older frontend paths may read either.

## Summary Rules

The AI summary must stay under 800 Chinese characters and answer:

- What happened?
- Why is it hot now?
- What does the main article/source say?
- What are the main attitudes in the comments?
- What evidence was unavailable or blocked?

Do not claim article reading, video viewing, image understanding, or full-comment coverage unless the run actually captured that evidence.

## Field Notes

- Baidu board links usually lead to `www.baidu.com/s?...&wd=<topic>`. Preserve the original board link and also store the normalized search URL.
- The full realtime board is best parsed from the server-rendered `s-data` payload. CDP should still open ShadowBot first, but if hydrated DOM drops the `s-data` comment, fetch the board HTML and parse `s-data` rather than trusting loose DOM links.
- Reject navigation and widget rows such as `查看更多>` when DOM fallback is unavoidable.
- Baidu search result pages contain related searches and interaction widgets. Do not select `www.baidu.com/s?...`, Baike, image/video/map/tieba/zhidao/wenku, `弹幕互动`, or `换一换` as the main article.
- Baidu search pages may expose a comment/interaction block above normal results. Treat those comments as Baidu-visible comments, not article-site comments.
- Article links may be redirected through Baidu. Resolve redirects and store both Baidu link and final URL.
- Some results are snippets only or block direct article extraction. Save the row as `partial` with a clear `main_article.extraction_status`.
- PowerShell can display Chinese incorrectly. Verify Chinese with Node, browser UI, or database/API JSON before assuming stored text is corrupt.

## Validation Checklist

After a full run, verify:

- Active Baidu rows match the board count requested, usually 30.
- Ranks are unique and sorted ascending.
- Every row has title, rank, and either numeric `score` or original `heat_text`.
- Every row has `raw_payload.board_item.search_url`.
- Every completed row has an `ai_summary.summary` of 800 Chinese characters or fewer.
- `raw_payload.top_comments.length` matches the number of comments saved for that hotspot.
- Short comment/article captures are explained by `comment_fetch.failures` or `main_article.extraction_status`.
- Cookie values are absent from logs, JSON output, and database rows.
- Temporary ShadowBot runtime profiles under `output/` are removed unless explicitly preserved.

For detailed implementation notes and known fixes, read [references/baidu-hotsearch-pipeline.md](references/baidu-hotsearch-pipeline.md).
