---
name: douyin-blogger-deep-capture
description: Use for D:\media-coding Douyin benchmark blogger profile deep capture when Codex must combine low-risk CDP metadata scraping, rolling 2-3 post micro-batches, immediate local video caching before temporary Douyin CDN links expire, anti-bot-safe desktop comment reading, and local video understanding for blogger_posts. Trigger for Douyin blogger homepage/profile work, guichu8888 / Gui Chu Bi Ji, blogger_posts media_cache/content_evidence, staged Douyin comments/videos, or rolling micro-batch Douyin capture.
---

# Douyin Blogger Deep Capture

## Core Rule

Run Douyin blogger work as rolling micro-batches, not as one big 40-post media-link queue. Douyin CDN video URLs can expire within minutes, so never collect all temporary video links first and download them later.

Never trust "looks like a video" alone. Every captured post must pass an author guard before writing or using it: `raw_payload.author.sec_uid` must equal the target blogger `platform_user_id` / profile `sec_uid`. If author evidence is missing or mismatched, mark it as non-target and do not save comments, cache new media, or analyze it as the blogger's content.

Use fast CDP scripts for stable low-risk metadata. For link-sensitive work, process 2 posts by default and 3 at most: refresh or use media URLs, immediately cache videos locally, and read comments for the same small batch before moving to the next batch.

Use visible desktop/computer-control style operation for comment reading because comments are the highest anti-bot risk. Use local media analysis only after the video has been cached.

Stop immediately for login, QR scan, SMS, CAPTCHA, slider puzzle, risk verification, or suspicious redirects. Ask the user to complete the challenge in the visible Douyin/ShadowBot browser. Never bypass or solve verification automatically.

## Confirmed Defaults

- Default smoke/first milestone scope: first 40 posts. Full-profile target can be 326 posts when explicitly requested.
- Rolling batch size: default 2 posts; max 3 posts while stable; reduce to 1 after any risk signal.
- Comments: target up to 50 real comments per video, but accept the maximum actually visible/loaded after safe scrolling. Do not force 50 by aggressive retrying.
- Comment workers: only one active Douyin comment-reading worker/session at a time.
- Video caching: download immediately after a fresh CDN URL is available.
- Video analysis: default to local `whisper.cpp`; OpenAI transcription is optional fallback only.
- Local video cache: keep long term under `output/media-cache/douyin/bloggers/<blogger_id>/<aweme_id>/`.
- Existing official app entry for this repo remains `http://localhost:3000/`; do not reconnect React TS migration files unless explicitly asked.

## Resume And Checkpoint Rules

Treat the database and local cache as the checkpoint. Long runs over 326 posts will be interrupted by verification, timeouts, database restarts, or network issues; never restart from the beginning unless the user explicitly asks.

A post is eligible for continuation only when it passes the author guard. Ignore old polluted rows whose `raw_payload.author.sec_uid` does not match the blogger.

Completion checks:

- Metadata complete: `blogger_posts` row exists and author guard passes.
- Media cache complete: `raw_payload.media_cache` contains a `cached` video entry whose local file still exists, or the local file exists at `output/media-cache/douyin/bloggers/<blogger_id>/<aweme_id>/video.mp4`.
- Comment pass complete: comments exist for the post and `raw_payload.comment_capture.status` is `ok` with `requested_comment_limit >= 50`. If saved comments are below 50 after a safe deep scroll, treat that as "maximum currently loaded", not a failure.
- Video understanding complete: `raw_payload.content_evidence.video_understanding.status` is `analyzed`, with transcript and visual frame evidence.

For every resumed run, first query the next uncompleted author-guarded ids ordered by `published_at desc, id desc`, then pass those explicit ids through `BLOGGER_POST_IDS`. Do not run `BLOGGER_ID + limit` blindly for cache/comments/analysis because it may pick rows that are already complete.

If the first 40 posts are already complete and the user's target is the whole homepage, resume from post 41 onward: rerun metadata with a larger `DOUYIN_PROFILE_MAX_POSTS` such as `326`, then select only rows that are missing cache, a 50-target comment pass, or video understanding.

## Rolling Workflow

### 1. Stable Metadata Seed

Use the existing project CDP integration and project script:

```powershell
$env:DOUYIN_PROFILE_BLOGGER_ID='97'
$env:DOUYIN_PROFILE_MAX_POSTS='40'
$env:DOUYIN_PROFILE_COMMENT_LIMIT='5'
$env:DOUYIN_PROFILE_DETAIL_POST_OFFSET='0'
$env:DOUYIN_PROFILE_DETAIL_POST_LIMIT='0'
$env:DOUYIN_PROFILE_COMMENT_SCROLL_ROUNDS='0'
$env:DOUYIN_PROFILE_DOWNLOAD_MEDIA='0'
npm run scrape:douyin-profile
```

This stage should write `blogger_posts` with platform post id, webpage URL, publish copy/time, and interaction counts. It should not open comment panels or download media.

This stage may capture temporary media URL hints, but do not trust them for later bulk download.

If fewer than the requested target posts are found, do not assume the profile is exhausted. Douyin profile pages may need repeated downward scrolling / pagination before the next real blogger batch appears, and recommendation videos may appear in between. Continue loading while raw video payloads or DOM video cards are still increasing, then filter by target author. Do not stop only because the author-matched count is briefly unchanged.

If normal JavaScript scrolling stalls, use more human-like page loading through CDP: bring the page to front, focus it, dispatch real mouse-wheel events over the video grid, and occasionally send `PageDown`. This was required to move from 21 confirmed `guichu8888` posts to the first 40 confirmed posts.

When metadata is refreshed, preserve existing post-processing evidence in `raw_payload`: `media_cache`, `comment_capture`, `comment_capture_history`, and `content_evidence`. Metadata refresh must never wipe completed local cache, comments progress, transcripts, frames, or video summaries.

If `risk_verification_required` appears, run:

```powershell
$env:DOUYIN_PROFILE_BLOGGER_ID='97'
npm run login:douyin-profile-shadowbot
```

Then ask the user to finish verification before retrying with a smaller batch.

### 2. Select A Micro-Batch

Pick the next 2 post ids that still need media cache or comments and have passed the author guard. Use 3 only when the account has been stable for several batches.

Before selecting ids, query or inspect `blogger_posts.raw_payload.author.sec_uid`. For `guichu8888`, it must be `MS4wLjABAAAAi_8vz_cYS4P1eGGZl4Z33w7fhI8PtkKMlLlHGSxS-08`. Ignore old rows that are already polluted by recommendation videos; do not continue work from those rows unless the user explicitly asks to clean them.

```powershell
$env:BLOGGER_POST_IDS='65,66'
```

If any risk signal appears, reduce the next batch to one post:

```powershell
$env:BLOGGER_POST_ID='65'
```

Only move to the next 2-3 posts after both media cache and comment reading for the current batch finish or fail with truthful status.

For full-profile continuation, generate ids from database state, not memory. Example selector intent: "author matches target, ordered newest to oldest, and missing cached media OR missing comment pass with requested limit 50 OR missing analyzed video understanding." 已完成的 ids should be skipped automatically.

### 3. Immediate Local Video Cache

Treat links this way:

- Share link: entry only; resolve/store as evidence, not as playable media.
- Web video URL: stable canonical `blogger_posts.url`, like `https://www.douyin.com/video/<aweme_id>`.
- Temporary CDN URL: only valid downloadable media source; download immediately.

Run the by-post or micro-batch media cache script:

```powershell
$env:BLOGGER_POST_IDS='65,66'
npm run cache:blogger-post-media
```

The script should first try existing CDN/media URLs. If they fail or are expired, refresh one detail page through CDP and retry immediately, not at the end of a 40-post queue.

Record successful cache evidence in `blogger_posts.raw_payload.media_cache` and append verified `/api/media-cache/...` URLs to `media_urls`. Failed downloads must stay as `download_failed` evidence, not fake playable paths.

### 4. Desktop Comment Reading

Use Codex desktop/computer-control or visible browser control to read comments one video at a time inside the small batch. The target is "up to 50"; partial real comments are acceptable and better than triggering risk control.

Recommended behavior:

- Use one active comment-reading worker/session only.
- Open only the canonical page `https://www.douyin.com/video/<aweme_id>`; do not use `iesdouyin.com/share/video/...` for detail reading.
- Before saving comments, verify the detail payload author still matches the target blogger.
- Open the current video detail page visibly.
- Wait like a user, open the comment panel, scroll lightly, capture visible/network comments.
- To get closer to 50, scroll inside the comment panel, not just the main page. Use slower repeated wheel/PageDown-like movement, longer waits, and one post per run after any risk signal.
- Save only clean top-level comments to `comments` with `blogger_post_id`.
- Write progress into `blogger_posts.raw_payload.comment_capture`.
- Cool down between videos.

Current script:

```powershell
$env:BLOGGER_POST_IDS='65,66'
$env:DOUYIN_COMMENT_LIMIT='50'
$env:DOUYIN_COMMENT_COOLDOWN_MS='20000'
npm run scrape:blogger-post-comments-desktop
```

Use these statuses:

- `ok`
- `no_comments`
- `risk_verification_required`
- `comment_panel_not_found`
- `network_payload_missing`
- `cdp_timeout`
- `runtime_unavailable`

Never keep retrying comments after risk verification. Stop and ask for human verification.

If a post returns fewer than 50 comments with `status: ok`, do at most one later deep-comment pass with higher `DOUYIN_COMMENT_SCROLL_ROUNDS` (for example 15-25) and longer cooldown. If it still returns fewer than 50, record the real count and continue; do not keep hammering the same video.

### 5. Safe Parallelism

The safest faster pattern is two workers per micro-batch:

- Worker A: media cache/download. It may run in parallel only when it is downloading from already captured URLs or local cache evidence.
- Worker B: comment reading. It must stay single-session and process posts one by one.

If Worker A needs to open Douyin to refresh expired media URLs, do that before Worker B starts for that batch, or pause Worker B until the media refresh is done. Avoid two simultaneous Douyin browser sessions on the same account.

Do not run two comment workers at once. Do not run video understanding while a Douyin browser risk-sensitive step is active unless it only uses already cached local files.

### 6. Local Video Understanding

Run this after all rolling batches have cached videos and collected comments. Use local cached media first. Extract audio, transcribe, extract key frames, analyze frames, and merge the final result into `blogger_posts.raw_payload.content_evidence`.

```powershell
$env:BLOGGER_POST_IDS='<comma-separated ids>'
$env:DOUYIN_STT_ENGINE='whisper.cpp'
npm run analyze:blogger-post-content
```

Store:

- `content_evidence.video_content_summary`
- `content_evidence.audio_transcript`
- `content_evidence.audio_source`
- `content_evidence.visual_timeline`
- `content_evidence.visual_frame_paths`
- `content_evidence.video_understanding.status`
- `content_evidence.video_understanding.limitations`

Do not present visual-only guesses as complete if audio is required and missing. Use `missing_evidence` honestly.

## Implementation Guidance

For concrete module names, fields, tests, and landing order, read `references/implementation-plan.md`.

Prefer narrow scripts and reusable helpers over expanding `scrape-douyin-profile.ts` into a giant all-in-one runner.

Recommended landing order:

1. Add or update media-cache-by-post script for micro-batch ids.
2. Add or update one-video desktop comment capture script for micro-batch ids, still sequential inside the script.
3. Add a micro-batch orchestrator only after media cache and comments work independently.
4. Extract reusable video-understanding helper from `analyze-douyin-creator-videos.ts`.
5. Add `analyze-blogger-post-content.ts`.

## Validation

If code changes touch entry, legacy UI, or Douyin capture behavior, run at least:

```powershell
npm test -- src/tests/douyin-profile-cdp.test.ts src/tests/blogger-scrape-handlers.test.ts src/tests/blogger-legacy-ui.test.ts src/tests/phase2-api.test.ts src/tests/app-html-legacy-entry.test.ts src/tests/hotspot-platform-tabs.test.ts
npm run typecheck
```

For media-cache or video-understanding scripts, also verify:

- local file exists and is larger than an error body
- `/api/media-cache/...` returns `200` and a video content type
- `blogger_posts.raw_payload.media_cache` records success/failure truthfully
- `content_evidence.video_understanding.status` matches available evidence
