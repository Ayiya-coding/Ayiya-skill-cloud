---
name: webo-cdp
description: Weibo hot-search capture skill for reliable scraping of current Weibo 热搜, each topic detail page's first/featured post, real repost/comment/like counts, media-aware summaries, and hot comments. Use when the user asks to refresh, diagnose, or build a Weibo hot-search crawler/database/frontend pipeline, especially when accuracy depends on logged-in Weibo pages, ShadowBot/影刀 browser login state, s.weibo.com detail pages, CDP browser automation, or avoiding ajax/statuses/search wrong-result fallbacks.
---

# webo+CDP

## Core Rule

Treat the logged-in `s.weibo.com/weibo?...` hot-search detail page as the source of truth for the first/featured Weibo post. Do not use `https://weibo.com/ajax/statuses/search?q=...&xsort=hot` as the primary source; it often returns a different search stream and causes wrong authors, wrong engagement counts, and missing comments.

Use this pipeline:

1. Fetch the current hot list from `https://weibo.com/ajax/statuses/hot_band` plus the pinned government item from `https://weibo.com/ajax/side/hotSearch`.
2. Build each topic detail URL as `https://s.weibo.com/weibo?q=<topic>&t=31&band_rank=<rank>&Refer=top`.
3. Open the detail URL with a logged-in ShadowBot/影刀 browser runtime through CDP and parse the first real feed card:
   - `mid`, `uid`, author, text, first-card post URL
   - visible media card text, image/video URLs, page "智搜/AI摘要" text when present
4. Use the parsed `mid` with `https://weibo.com/ajax/statuses/show?id=<mid>` to confirm author, canonical post URL, created time, text, repost count, comment count, like count, and long text.
5. Use `https://weibo.com/ajax/statuses/buildComments` with `id=<mid>`, `uid=<uid>`, `flow=0/1`, `max_id`, and `max_id_type` to fetch hot comments. Deduplicate, sort by like count, and keep up to 50 comments.
6. Write both the database comments table and `raw_payload.top_comments`, because legacy/static frontends may read either.
7. Store missing collect/favorite counts as `"-"` unless a reliable platform source exists.

## ShadowBot Login State

Prefer the machine's ShadowBot browser login state for Weibo:

- Default executable: `D:\Program Files (x86)\ShadowBot\ShadowBot Browser\Application\ShadowBotBrowser.exe`
- Default profile: `%LOCALAPPDATA%\ShadowBotBrowser\User Data`
- Required cookies: `SUB`, `SUBP`; useful extras include `WBPSESS`, `XSRF-TOKEN`, `ALF`, `SCF`.

Never store or print cookie values. It is safe to record cookie names, counts, and whether `SUB/SUBP` are present.

To avoid locking the user's real browser profile, copy only minimal profile files into a temp runtime profile:

- `Local State`
- `Default/Preferences`
- `Default/Secure Preferences`
- `Default/Network/Cookies`

Launch the temp profile with `--remote-debugging-port=<open-port>`, use CDP to read cookies and navigate detail pages, then kill the ShadowBot process tree and delete the temp profile.

Fallbacks:

- `WEIBO_COOKIE=<cookie header>`: use explicit cookies from env.
- `WEIBO_AUTH_SOURCE=visitor`: visitor cookies only for smoke tests; do not expect complete comments or logged-in detail pages.

## Zhisou Content Summary

For the frontend `内容简介`, prefer Weibo detail-page "智搜/AI摘要" over local video understanding. Store the full raw Zhisou text in `raw_payload.zhisou_summary.raw_text`, then run:

```powershell
npm run summarize:weibo-zhisou
```

The generated `raw_payload.zhisou_summary.content_summary` is the only text that should be shown in the frontend `内容简介`.

Summary rules:

- Use only the stored Zhisou raw text as input.
- Output pure event content only; do not mention Zhisou, AI, summary generation, source, tool, author analysis, or backend process.
- Keep it under 800 Chinese characters.
- Use neutral third-person wording and factual event order.
- Remove links, `@` handles, `#topic#` markup, emojis, ads, and follow/forward calls.
- Do not add facts, dates, names, places, numbers, or claims that are absent from the Zhisou text.
- If the raw text is missing or unusable, write exactly `暂无内容简介。`.

## Database Contract

For the `media-coding` project, use or maintain:

- Script: `src/server/scripts/scrape-weibo-hotsearch.ts`
- Command: `npm run scrape:weibo-hotsearch`
- Summary command: `npm run summarize:weibo-zhisou`
- Optional filters:
  - `WEIBO_HOT_LIMIT=3` for smoke tests
  - `WEIBO_TOPIC_FILTER="标题1|标题2"` for targeted补抓
  - `WEIBO_COMMENT_LIMIT=50`
  - `WEIBO_ZHISOU_SUMMARY_LIMIT=51`
  - `WEIBO_ZHISOU_HOTSPOT_IDS="1020,1021"`
  - `WEIBO_ZHISOU_SUMMARY_FORCE=1`
- API verification:
  - `GET http://127.0.0.1:8787/api/hotspots?platform=weibo&status=active&limit=100&sort=rank&direction=asc&include_raw=true`

Expected `hotspots.raw_payload` shape:

- `capture`: date, captured_at, source, `selection_source`, login-state metadata
- `detail_url`: hot-search detail page URL
- `detail_page_post`: parsed s.weibo first card
- `zhisou_summary`: full raw Zhisou text plus pure-content frontend summary
- `top_post`: confirmed status details, counts, post URL, summary, media descriptions
- `top_comments`: up to 50 top comments for frontend use
- `comment_summary`: clustered viewpoints from sampled comments
- `comment_fetch`: requested/sample count, total number, sources
- `collect_count`: `"-"` when unavailable

Expected `selection_source`:

- `s_weibo_dom`: normal topics, parsed from detail page first card
- `hotgov_mid`: pinned official/government item with a direct `mid`
- `fallback_search_api`: should be 0 in final quality checks; treat as a defect unless the user accepts degradation

## Validation Checklist

After any scrape, verify:

- Active Weibo rows match the intended hot list count, usually 51.
- No `fallback_search_api` rows remain.
- Ranks are unique and cover the expected range after targeted补抓.
- `raw_payload.top_post.author_name` matches `raw_payload.detail_page_post.author_name` for `s_weibo_dom` rows.
- `raw_payload.top_post.comment_count` is the real Weibo total count, not the sample length.
- `raw_payload.top_comments.length` is 50 where Weibo exposes enough comments; explain shortfalls when the platform only returns fewer comments or the post has few/no comments.
- Frontend API returns Chinese correctly through `fetch().json()`; ignore PowerShell mojibake unless Node/DB also show bad text.
- ShadowBot temp runtime profiles and processes are cleaned from `output/shadowbot-weibo-runtime-*`.

For detailed implementation notes and known fixes, read [references/weibo-hotsearch-pipeline.md](references/weibo-hotsearch-pipeline.md).
