# webo+CDP Weibo Hot-Search Pipeline Reference

## Why This Exists

The fragile part of Weibo hot-search capture is identifying the correct "first/featured post" for each hot topic. The Weibo search AJAX endpoint can return unrelated posts from a broader search stream. In one observed failure, topic `#豆包付费#` was stored as coming from `艾泽拉斯旧梦`, while the user-visible hot-search detail page first post was actually from `漂亮虎咚咚` with far higher repost/comment/like counts and real comments. The fix is to parse the logged-in `s.weibo.com` detail page first card, then confirm with `statuses/show`.

## Correct End-To-End Flow

1. Load or create a logged-in session.
   - Prefer ShadowBot/影刀 cookies.
   - Verify `SUB` and `SUBP`.
   - Keep cookie values out of logs and DB.

2. Fetch the hot list.
   - `https://weibo.com/ajax/statuses/hot_band`
   - `https://weibo.com/ajax/side/hotSearch` for the pinned item.
   - Optional `xcrawl` capture of `https://s.weibo.com/top/summary?cate=realtimehot` is useful as evidence but not enough for post/comment data.

3. Build detail URLs.
   - Use `word_scheme` when available, otherwise `#${title}#`.
   - Add `t=31`, `Refer=top`, and `band_rank` when known.

4. Parse detail page first card through CDP.
   - Navigate the logged-in ShadowBot page to the detail URL.
   - Evaluate a DOM extractor against `.card-wrap[action-type="feed_list_item"], .card-wrap`.
   - Find the first card with `mid`, author, and body text.
   - Extract links, stats, media, raw card text, and page AI summary around `智搜回答`.

5. Confirm with status API.
   - Call `https://weibo.com/ajax/statuses/show?id=<mid>`.
   - Use the returned `user`, `mblogid`, `created_at`, counts, and text as canonical.
   - If `isLongText`, call `https://weibo.com/ajax/statuses/longtext?id=<mid>`.
   - Backfill/confirm `detail_page_post.author_name`, `author_url`, `post_url`, and counts from this API.

6. Fetch comments.
   - Endpoint: `https://weibo.com/ajax/statuses/buildComments`
   - Parameters: `flow`, `is_reload=1`, `id=<mid>`, `is_show_bulletin=2`, `is_mix=0`, `max_id`, `max_id_type`, `count=50`, `uid=<uid>`, `fetch_level=0`, `locale=zh-CN`
   - Try `flow=0` and `flow=1`.
   - Follow `max_id` and `max_id_type` for several pages until 50 unique comments or exhaustion.
   - Deduplicate by comment id or text fallback, sort by like count, keep 50.

7. Write data.
   - Upsert `hotspots` by `(platform, platform_hotspot_id)`.
   - Delete and upsert comments for the hotspot id.
   - Store comment samples both in `comments` table and `raw_payload.top_comments`.
   - Set `collect_count` to `"-"` when absent.

8. Archive carefully.
   - Only archive old Weibo rows after a full hot-list run.
   - Do not archive on targeted补抓 (`WEIBO_TOPIC_FILTER`), or a补抓 will make the rest of the active list disappear.

## Known Problems And Fixes

### Wrong author and wrong comments

Cause: using `ajax/statuses/search?q=...&xsort=hot` as primary source.

Fix: parse `s.weibo.com` detail-page first card via CDP. Use search API only as temporary diagnostic fallback, and final QA should require fallback count 0.

### CDP hangs or ShadowBot target goes stale

Cause: browser page target can stop responding during navigation/evaluation.

Fix:

- Add a per-CDP-command timeout.
- Catch detail-parse failures per topic so the whole scrape does not hang.
- Kill the ShadowBot process tree on Windows with `taskkill /PID <pid> /T /F`.
- Remove `output/shadowbot-weibo-runtime-*` after the process exits.

### Comments do not fill to 50

Cause: only requesting one page, missing `max_id_type`, or Weibo exposes fewer hot comments than total comments suggest.

Fix:

- Include `max_id_type` in pagination.
- Fetch multiple pages across `flow=0` and `flow=1`.
- Deduplicate and sort by like count.
- If still under 50, record the true count and explain that Weibo did not expose more unique hot comments.

### Targeted补抓 corrupts active list or rank order

Cause: targeted runs use a different current hot-list snapshot or titles no longer exist in the current hot list.

Fix:

- Do not archive old rows during targeted补抓.
- Preserve full-snapshot ranks when補抓 is only meant to replace details/comments.
- If ranks become duplicated, rerun a full snapshot or restore ranks from the latest full snapshot.
- For topics no longer in the hot list, allow manual title items with no rank, then assign the previous full-snapshot rank if preserving an old list.

### PowerShell Chinese mojibake

Cause: PowerShell console/log decoding may display UTF-8/UTF-16 text incorrectly.

Fix: verify Chinese through Node `fetch().json()`, Node DB queries, or the browser frontend. Do not assume DB corruption from PowerShell mojibake alone.

### Media summaries overclaim visual reading

Cause: image/video posts may have little plain text.

Fix: use available vision if configured; otherwise combine post text, media card text, page `智搜/AI摘要`, and comment attitudes. Say what was and was not directly inspected.

## Useful Verification Queries

```js
import pg from 'pg';
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const summary = await pool.query(`
  select
    count(*)::int as active_count,
    count(*) filter (where raw_payload->'capture'->>'selection_source'='s_weibo_dom')::int as dom_count,
    count(*) filter (where raw_payload->'capture'->>'selection_source'='hotgov_mid')::int as hotgov_count,
    count(*) filter (where raw_payload->'capture'->>'selection_source'='fallback_search_api')::int as fallback_count,
    sum(jsonb_array_length(coalesce(raw_payload->'top_comments','[]'::jsonb)))::int as raw_comment_total,
    count(*) filter (where jsonb_array_length(coalesce(raw_payload->'top_comments','[]'::jsonb)) >= 50)::int as rows_with_50_comments
  from hotspots
  where platform='weibo' and status='active'
`);
console.table(summary.rows);
await pool.end();
```

```js
const res = await fetch('http://127.0.0.1:8787/api/hotspots?platform=weibo&status=active&limit=5&sort=rank&direction=asc&include_raw=true');
const body = await res.json();
console.log(body.data.items.map((item) => ({
  rank: item.rank,
  title: item.title,
  author: item.raw_payload?.top_post?.author_name,
  comments: item.raw_payload?.top_comments?.length,
})));
```

## Completion Criteria

A run is production-quality when:

- `hotspots_upserted` equals the current hot-list size.
- `failures` is empty, or each failure is explained and explicitly accepted by the user.
- `fallback_search_api` count is 0.
- The top sample that previously failed, such as `豆包 付费`, matches the user-visible detail-page first author and has real comments.
- Tests relevant to API/repositories pass.
- Temp ShadowBot runtime directories are gone.
