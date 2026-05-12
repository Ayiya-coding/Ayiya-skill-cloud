# Baidu Hot Search CDP Pipeline Reference

## Purpose

Use ShadowBot Browser CDP to capture the current Baidu 热搜榜, then enrich each topic with Baidu search result evidence, main article text, AI summary, and comments before storing data in the `media-coding` database.

The important idea is simple: the hot board tells us what is hot; the Baidu search page and main article tell us what the hot topic means; the comment modules tell us public reaction. Keep those layers separate in `raw_payload` so later debugging can see where each field came from.

## Correct End-To-End Flow

1. Load or create a ShadowBot CDP runtime.
   - Prefer a copied temporary profile.
   - Record browser executable path, profile source, cookie count, login presence, and verification state.
   - Never log cookie values.

2. Open the board.
   - Primary URL: `https://top.baidu.com/board?tab=realtime`
   - Fallback URLs: `https://top.baidu.com/board`, `https://top.baidu.com/board?tab=homepage`
   - `tab=realtime` exposes the full realtime board, usually 51 rows. The homepage URLs expose only the compact homepage card.

3. Extract board rows.
   - Prefer the server-rendered `s-data` payload from the board HTML.
   - Keep rank, title, heat index, heat text, badges, image URL if visible, board link, and normalized Baidu search URL.
   - Deduplicate by title, then rank. A full run should keep the rank order shown on the page.
   - If ShadowBot CDP opens a hydrated DOM where `document.documentElement.outerHTML` no longer contains the `s-data` comment, fetch the board HTML after opening ShadowBot and parse `s-data` from that response.
   - DOM fallback must reject utility rows such as `查看更多>` and rank-only strings.

4. Open each topic search page.
   - Prefer the board link if present.
   - Fallback: `https://www.baidu.com/s?wd=<encoded title>&sa=fyb_hp_news&rsv_dl=fyb_hp_news`
   - Capture search-page evidence: Baidu answer/news card, top results, snippets, source names, publish times, related searches, and visible comments.

5. Select the main article/result.
   - Prefer a result that is clearly about the same hot topic and has a source/publish time.
   - Prefer authoritative or original news sources over aggregators.
   - Avoid ads, unrelated encyclopedia pages, or broad search results that do not explain the event.
   - Reject related searches and widgets: `www.baidu.com/s?...`, Baike, image/video/map/tieba/zhidao/wenku, `弹幕互动`, `换一换`, and `相关搜索`.
   - If the top Baidu answer card already contains enough context but no article opens, store that as `main_article.extraction_status = "baidu_answer_only"`.

6. Extract article content.
   - Resolve Baidu redirect links.
   - Use reader-style extraction from DOM text, article tags, JSON-LD, or known news containers.
   - Keep title, source, published_at, resolved_url, text_excerpt, and extraction_status.
   - If the page blocks access, records only snippets and explain the block.

7. Collect comments.
   - Capture Baidu-visible comments from the search page interaction module when present.
   - Also capture comments from the opened article page when the article exposes them.
   - Use visible DOM and authenticated network responses. Continue scrolling or pagination until no new comment IDs/texts appear.
   - Deduplicate by platform comment ID when available, otherwise by exact content plus author.
   - Store all exposed comments unless `BAIDU_COMMENT_LIMIT` is set for a smoke test.

8. Summarize with AI.
   - Input should include board title/rank/heat, Baidu answer text, selected article text, top result snippets, and collected comments.
   - Output must be concise Chinese under 800 characters.
   - Include limitations when article text or comments were gated.
   - Default to `BAIDU_AI_ANALYZER=codex` when available.
   - If `BAIDU_AI_ANALYZER=none`, create a deterministic plain-text fallback summary from captured evidence and mark analyzer as `none`.

9. Persist database rows.
   - Upsert `hotspots` by `(platform, platform_hotspot_id)`.
   - Use `platform = "baidu"`.
   - Recommended `platform_hotspot_id`: stable hash or slug of normalized title plus board type, for example `homepage:<sha1(title)>`.
   - Set `title`, `url`, `rank`, `score`, `heat_text`, `status = "active"`, `last_seen_at`.
   - Replace that hotspot's `comments` rows and store the same comments in `raw_payload.top_comments`.
   - Archive old Baidu rows only after a complete full-board run. Never archive during targeted refill.

## Suggested Database Mapping

`hotspots`:

- `platform`: `baidu`
- `platform_hotspot_id`: `homepage:<stable-title-id>`
- `title`: board title
- `description`: AI summary or Baidu answer excerpt
- `url`: normalized Baidu search URL
- `rank`: board rank
- `score`: numeric heat index when available
- `heat_text`: original heat text, such as `热搜指数：101057`
- `category`: `热搜榜`
- `tags`: badges plus source tags, for example `["热", "baidu_answer"]`
- `raw_payload`: full capture evidence

`comments`:

- `hotspot_id`: saved hotspot id
- `platform`: `baidu`
- `platform_comment_id`: Baidu/article comment id when available, otherwise stable hash of source URL, author, and text
- `author_name`: comment author if visible
- `content`: comment text
- `liked_count`: parsed like/up count, default 0
- `reply_count`: parsed reply count, default 0
- `published_at`: parsed time when visible
- `raw_payload`: source URL, source type, DOM/network evidence, raw counts

## ShadowBot CDP Implementation Hints

Use the same pattern as `webo-cdp`:

- Find an open debug port.
- Copy minimal profile files into `output/shadowbot-baidu-runtime-*`.
- Launch ShadowBot Browser with `--remote-debugging-port=<port>` and the temp profile.
- Attach over CDP.
- Apply per-command timeouts so one bad topic does not hang the whole run.
- Catch per-topic failures and keep the full run moving.
- Kill the ShadowBot process tree and delete temp profiles at the end unless `BAIDU_KEEP_PROFILE=1`.

Suggested extraction selectors should be treated as hints, not hard contracts:

- Board rows: links/cards under the 热搜榜 section; require visible rank text plus title text.
- Heat text: text matching `热搜指数` or a nearby numeric heat block.
- Search results: result containers with title links, source text, publish time, and snippets.
- Comments: containers near `弹幕互动`, `评论`, `大家在说`, or network payloads containing comment-like text and like counts.

When selectors change, update this file with the new selectors and the failure symptom.

## Known Problems And Fixes

### Board page returns partial rows or `查看更多>` appears as a topic

Cause: using homepage board URLs, or trusting loose DOM links after Baidu's hydrated page removed the original `s-data` comment.

Fix: use `https://top.baidu.com/board?tab=realtime`, parse the server-rendered `s-data` payload, and reject utility rows such as `查看更多>` in DOM fallback.

### Search result opens another Baidu search page instead of an article

Cause: related-search links and interaction widgets can be parsed before real article results.

Fix: filter out `www.baidu.com/s?...`, `弹幕互动`, `换一换`, `相关搜索`, Baike, image/video/map/tieba/zhidao/wenku, then choose the best remaining result.

### Search page has comments but no article body

Cause: Baidu answer/news card is available, but clicked article blocks extraction or uses heavy client rendering.

Fix: store Baidu answer and snippets, mark `main_article.extraction_status = "blocked_or_unreadable"`, and summarize only from captured evidence.

### "All comments" is impossible to prove

Cause: Baidu or article sites may hide total comments, require login, or paginate behind private APIs.

Fix: define completion as "all comments exposed through visible DOM or authenticated network responses until exhaustion." Record `comment_fetch.exhausted = true/false`, `collected`, and failure reason.

### CAPTCHA or abnormal traffic

Cause: Baidu detected automated traffic.

Fix: stop, ask the user to complete verification in ShadowBot, then retry with the same browser state. Do not bypass CAPTCHA with unapproved third-party services.

### Chinese text looks broken in PowerShell

Cause: terminal encoding display, not necessarily bad data.

Fix: verify through Node database queries, API JSON, or frontend rendering before changing encoding code.

## Verification Queries

Use Node rather than PowerShell text output when checking Chinese:

```js
import pg from "pg";

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const summary = await pool.query(`
  select
    count(*)::int as active_count,
    count(*) filter (where rank is not null)::int as ranked_count,
    count(*) filter (where score is not null or heat_text is not null)::int as heat_count,
    count(*) filter (where raw_payload->'ai_summary'->>'summary' is not null)::int as summarized_count,
    sum(jsonb_array_length(coalesce(raw_payload->'top_comments','[]'::jsonb)))::int as raw_comment_total
  from hotspots
  where platform='baidu' and status='active'
`);
console.table(summary.rows);
await pool.end();
```

```js
const res = await fetch("http://127.0.0.1:8787/api/hotspots?platform=baidu&status=active&limit=5&sort=rank&direction=asc&include_raw=true");
const body = await res.json();
console.log(body.data.items.map((item) => ({
  rank: item.rank,
  title: item.title,
  heat: item.heat_text ?? item.score,
  summaryLength: item.raw_payload?.ai_summary?.summary?.length ?? 0,
  comments: item.raw_payload?.top_comments?.length ?? 0,
})));
```

## Completion Criteria

A run is production-quality when:

- The requested Baidu hot-search rows were saved as active rows.
- Ranks are unique for a full-board run.
- Each row has rank, title, heat evidence, search URL, and raw board payload.
- Each completed row has a main evidence source and an AI summary under 800 Chinese characters.
- Comment counts in `comments` and `raw_payload.top_comments` agree.
- Every partial row explains exactly what was blocked or unavailable.
- Temporary ShadowBot runtime directories are gone unless preserved for debugging.
- Any new blocker or selector change has been added back into this skill.
