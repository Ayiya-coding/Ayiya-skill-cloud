# Douyin Blogger Deep Capture Implementation Plan

## Existing Code To Reuse

- `src/server/integrations/douyin-profile-cdp.ts`
  - Reuse ShadowBot runtime setup, CDP helpers, payload extraction, risk detection, media cache validation.
- `src/server/scripts/scrape-douyin-profile.ts`
  - Reuse environment parsing and persistence flow for `blogger_posts` and `comments`.
- `src/server/scripts/launch-douyin-profile-shadowbot-login.ts`
  - Reuse for human verification handoff.
- `src/server/scripts/analyze-douyin-creator-videos.ts`
  - Reuse ffmpeg, whisper.cpp, frame extraction, Codex visual analysis, and summary synthesis patterns.
- `src/server/scripts/analyze-bilibili-hotspot-videos.ts`
  - Reuse more robust media-download/range-download patterns if direct Douyin CDN download is flaky.
- `src/server/repositories/blogger-posts.ts`
  - Reuse `upsertBloggerPosts`, `getBloggerPostIdsByPlatformPostIds`, and add narrow update helpers for raw payload merges.
- `src/server/repositories/comments.ts`
  - Reuse `upsertCommentsForBloggerPost`.
- `src/server/routes/media-cache.ts`
  - Reuse existing public media route.

## Proposed New Modules

### `src/server/integrations/douyin-post-cdp.ts`

Single-post browser helper.

Responsibilities:

- Open one `https://www.douyin.com/video/<aweme_id>` page.
- Capture detail payload and current media URLs.
- Capture comment network payloads or filtered visible DOM comments.
- Verify the detail payload author matches the target blogger before returning comments.
- Detect and report login/risk states.

Suggested exported function:

```ts
captureDouyinPostWithCdp({
  bloggerPost,
  commentLimit,
  commentScrollRounds,
  downloadMedia,
}): Promise<{
  postPatch: Partial<NormalizedPost>;
  freshMediaUrls: string[];
  comments: NormalizedComment[];
  warnings: string[];
  status: string;
}>
```

### `src/server/scripts/cache-blogger-post-media.ts`

Single-purpose media cache script. It must support micro-batch ids because Douyin CDN URLs expire quickly.

Inputs:

- `BLOGGER_POST_ID`
- or `BLOGGER_POST_IDS`
- or `BLOGGER_ID` plus a small limit

Flow:

1. Read target `blogger_posts`.
2. Try current `media_urls` first.
3. If media URLs fail or are expired, reopen only the current web video URL and refresh CDN URLs via `douyin-post-cdp`.
4. Download the fresh CDN URL immediately; do not queue refreshed URLs for later.
5. Call existing `cacheDouyinMediaAsset`.
6. Merge evidence into `raw_payload.media_cache`.
7. Append verified public URL to `media_urls`.

Failure labels:

- `media_cached`
- `media_url_expired`
- `media_download_failed`
- `media_refresh_required`
- `risk_verification_required`

### `src/server/scripts/scrape-blogger-post-comments-desktop.ts`

Desktop/computer-control comment script.

Inputs:

- `BLOGGER_POST_ID`
- or `BLOGGER_POST_IDS`
- `COMMENT_LIMIT=50`
- `COMMENT_SCROLL_ROUNDS=2`
- `POST_COOLDOWN_MS=20000`

Flow:

1. Accept `BLOGGER_POST_IDS`, but process posts sequentially inside the comment script.
2. Open visible video detail page.
3. Capture visible/network comments with light scrolling.
4. Upsert comments through `upsertCommentsForBloggerPost`.
5. Merge progress into `raw_payload.comment_capture`.

Recommended `comment_capture` shape:

```json
{
  "source": "codex_desktop_control",
  "requested_limit": 50,
  "saved_count": 7,
  "status": "partial",
  "last_run_at": "2026-05-05T00:00:00.000Z",
  "limitations": ["visible_comments_only"]
}
```

### `src/server/integrations/video-understanding.ts`

Reusable media analysis core extracted from `analyze-douyin-creator-videos.ts`.

Suggested exported function:

```ts
analyzeMediaForSummary({
  context,
  evidence,
  options,
  tools,
}): Promise<AnalysisEvidence>
```

Use `whisper.cpp` by default. Use OpenAI transcription only when configured and needed.

### `src/server/scripts/analyze-blogger-post-content.ts`

Blogger-post adapter for video understanding.

Inputs:

- `BLOGGER_POST_ID`
- or `BLOGGER_POST_IDS`
- or `BLOGGER_ID` plus `LIMIT`

Flow:

1. Read `blogger_posts`.
2. Prefer verified local media cache paths.
3. If no local media exists, ask the operator to run media cache first or optionally call media-cache refresh.
4. Run `analyzeMediaForSummary`.
5. Merge result into `raw_payload.content_evidence`.

## Link Strategy

Use three link roles:

- Share link: flexible user input; resolve it and store as evidence only.
- Web URL: stable canonical `blogger_posts.url`.
- CDN URL: temporary downloadable media URL; download immediately and do not rely on it later. Avoid collecting CDN URLs for more than 2-3 posts before caching.

Do not store share links or web-page links as playable `media_urls`.

## Author Guard Strategy

Every post must pass an author guard before it is treated as a target blogger post.

For blogger 97 / `guichu8888`, the expected Douyin `sec_uid` is:

```txt
MS4wLjABAAAAi_8vz_cYS4P1eGGZl4Z33w7fhI8PtkKMlLlHGSxS-08
```

Rules:

- During metadata normalization, filter out any `aweme` whose `author.sec_uid` does not match the target blogger `platform_user_id`.
- During single-post comment capture, always open `https://www.douyin.com/video/<aweme_id>`, not an `iesdouyin.com/share/video/...` URL.
- Before saving comments, confirm the detail payload for that `aweme_id` is authored by the target blogger.
- If author evidence is missing or mismatched, return a truthful status such as `post_author_mismatch` or `single_post_payload_missing`; do not save comments.
- Old polluted rows may remain in the database if the user asks not to clean them, but future batches must select only author-guard-passing rows.

## Database Strategy

No migration is required for the first implementation.

Use:

- `blogger_posts.url`
- `blogger_posts.platform_post_id`
- `blogger_posts.media_urls`
- `blogger_posts.raw_payload.media_cache`
- `blogger_posts.raw_payload.comment_capture`
- `blogger_posts.raw_payload.content_evidence`
- `comments.blogger_post_id`

Keep `comments` target exclusivity: when saving blogger comments, set only `bloggerPostId`; do not also set hotspot or IP post ids.

## Rolling Micro-Batch Operating Plan

Target: blogger 97. First milestone is 40 posts; full-profile continuation can target 326 posts.

1. Metadata only:

```powershell
$env:DOUYIN_PROFILE_BLOGGER_ID='97'
$env:DOUYIN_PROFILE_MAX_POSTS='40'
$env:DOUYIN_PROFILE_DETAIL_POST_LIMIT='0'
$env:DOUYIN_PROFILE_DOWNLOAD_MEDIA='0'
npm run scrape:douyin-profile
```

Profile loading rule: if fewer than 40 author-matched posts are found, keep scrolling/paginating while either the raw payload video count or DOM video card count is still increasing. Do not stop just because the author-matched count is temporarily flat; Douyin may load non-target recommendations before the next real blogger posts.

Fallback loading rule: if `window.scrollBy` / `scrollTop` alone stalls around the first page, use CDP human-like inputs: `Page.bringToFront`, focus the window, dispatch `Input.dispatchMouseEvent` with `type: "mouseWheel"` over the grid, and send occasional `PageDown` key events. This is the confirmed path that loaded posts 22-40 for `guichu8888`.

Metadata upsert rule: preserve existing `raw_payload.media_cache`, `raw_payload.comment_capture`, `raw_payload.comment_capture_history`, and `raw_payload.content_evidence` when refreshing post metadata. Low-risk metadata capture must update captions/times/metrics without wiping completed cache, comment progress, transcripts, frames, or summaries.

2. Select the next 2 post ids that still need cache or comments:

```powershell
$env:BLOGGER_POST_IDS='<id1>,<id2>'
```

Only select ids whose `raw_payload.author.sec_uid` matches the target blogger. Do not continue from recommendation-video rows already attached to the blogger by earlier buggy runs.

Resume selector rule: for long 326-post jobs, always select from database state. Skip any author-guarded post that already has cached local media, a successful comment pass with `requested_comment_limit >= 50`, and `content_evidence.video_understanding.status = analyzed`. Pass selected ids explicitly through `BLOGGER_POST_IDS`; do not rely on `BLOGGER_ID + LIMIT` for resumed cache/comment/analysis work.

Suggested SQL shape for the operator:

```sql
select bp.id
from blogger_posts bp
join bloggers b on b.id = bp.blogger_id
where bp.blogger_id = 97
  and bp.platform = 'douyin'
  and bp.raw_payload->'author'->>'sec_uid' = b.platform_user_id
  and (
    not exists (
      select 1 from jsonb_array_elements(coalesce(bp.raw_payload->'media_cache', '[]'::jsonb)) item
      where item->>'status' = 'cached'
    )
    or coalesce((bp.raw_payload->'comment_capture'->>'requested_comment_limit')::int, 0) < 50
    or coalesce(bp.raw_payload->'comment_capture'->>'status', '') <> 'ok'
    or coalesce(bp.raw_payload->'content_evidence'->'video_understanding'->>'status', '') <> 'analyzed'
  )
order by bp.published_at desc nulls last, bp.id desc
limit 3;
```

Use 3 ids only when the account is stable. Drop to 1 id after any risk signal.

3. Cache media immediately for the current micro-batch:

```powershell
$env:BLOGGER_POST_IDS='<id1>,<id2>'
npm run cache:blogger-post-media
```

4. Capture visible comments for the same micro-batch. The script should still process videos sequentially with cooldown:

```powershell
$env:BLOGGER_POST_IDS='<id1>,<id2>'
$env:DOUYIN_COMMENT_LIMIT='50'
$env:DOUYIN_COMMENT_SCROLL_ROUNDS='2'
$env:DOUYIN_COMMENT_COOLDOWN_MS='20000'
npm run scrape:blogger-post-comments-desktop
```

Comment depth rule: comment retrieval requires scrolling inside the comment panel. For the first safe pass use moderate rounds such as 8; to push closer to 50, run one later deep pass per video with 15-25 rounds, longer waits, and a single video per run. If the platform still returns fewer than 50 comments with `status=ok`, treat that as the maximum currently loaded and continue.

5. Repeat steps 2-4 until the first 40-post scope is done.

6. Analyze cached media after all rolling batches are complete:

```powershell
$env:BLOGGER_POST_IDS='<comma-separated completed ids>'
$env:DOUYIN_STT_ENGINE='whisper.cpp'
npm run analyze:blogger-post-content
```

## Parallel Agent Pattern

Use at most two workers per micro-batch:

- Worker A: media cache/download.
- Worker B: comment reading.

Safe cases:

- Worker A can run while Worker B reads comments only if Worker A is downloading already captured CDN URLs and is not opening a Douyin browser page.
- Worker B must use one visible/comment-reading session and process posts sequentially.

Unsafe cases:

- Do not run two comment workers.
- Do not open two Douyin browser sessions on the same account at the same time.
- If Worker A must refresh an expired CDN URL by opening Douyin, pause Worker B or do the media refresh before starting comments for that batch.
- Do not start the next micro-batch before both current-batch workers finish or report truthful failure.

## Test Points

- Metadata script does not open comments when detail limit is 0.
- Metadata normalizer filters recommendation videos whose `author.sec_uid` does not match the blogger.
- Single-post comment capture refuses to save comments when detail-page author mismatches the blogger.
- Media cache rejects HTML/403/tiny bodies.
- Local media file is playable and served by `/api/media-cache/...`.
- Comment rows are attached to the correct `blogger_post_id`.
- Duplicate comment capture does not duplicate rows.
- Video understanding writes `content_evidence.video_content_summary` only when evidence is enough.
- Missing audio or visual evidence writes `missing_evidence`, not a fake completed summary.

## Risk Controls

- Do not run comments and media downloads in the same browser pass.
- Do not gather temporary CDN URLs for all 40 posts before downloading.
- Process 2 posts per micro-batch by default, 3 at most, 1 after risk signals.
- Keep only one comment-reading worker active.
- Stop on any verification page.
- Prefer partial real comments over forced 50.
- Keep local video cache long term; clean only temp analysis files.
- Never fabricate media paths, comments, transcripts, or visual evidence.
