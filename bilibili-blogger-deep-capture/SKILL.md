---
name: bilibili-blogger-deep-capture
description: Use for D:\media-coding Bilibili (B站) UP主 profile deep capture when collecting all videos from a blogger's space, fetching metadata + engagement metrics via Bilibili public API, collecting top 50 comments per video, caching video media locally, and running local video understanding (subtitle/whisper transcription + visual frame analysis) for blogger_posts. Trigger for Bilibili UP主 homepage/space work, blogger_posts with platform=bilibili, media_cache/content_evidence for bilibili bloggers, or bilibili blogger video analysis.
---

# Bilibili Blogger Deep Capture

## Core Rule

Run Bilibili blogger work as rolling micro-batches. Although Bilibili API CDN URLs are generally more stable than Douyin, always process in batches of 5 videos (max 10 when stable) to avoid rate limiting and to checkpoint progress.

Bilibili public APIs do not require login for metadata and comments, but the space video list API (`/x/space/wbi/arc/search`) requires WBI signature. Always compute WBI signing parameters (`w_rid` and `wts`) before calling space APIs.

Every captured post must pass an author guard: `raw_payload.author.mid` must equal the target blogger's `platform_user_id` / space `mid`. If author evidence is missing or mismatched, skip the video.

Use the existing project database and scripts. Store blogger in `bloggers` table with `platform='bilibili'`, store posts in `blogger_posts` table. Reuse the existing video analysis pipeline from `analyze-bilibili-hotspot-videos.ts` patterns.

## Confirmed Defaults

- Default batch size: 5 videos; max 10 while stable; reduce to 2 after any rate-limit signal.
- Comments: target up to 50 real top-level comments per video via paginated API.
- Video caching: download audio + video DASH streams immediately after metadata collection.
- Video analysis: subtitle → whisper.cpp → OpenAI transcription fallback chain.
- Local video cache: `output/media-cache/bilibili/bloggers/<mid>/<bvid>/`.
- Video content summary: no word limit, aim for complete content representation.
- API rate limiting: 500ms between video detail/comment requests, 1000ms between space page requests.

## Resume And Checkpoint Rules

Treat the database and local cache as the checkpoint. Long runs will be interrupted by rate limits, network issues, or API errors; never restart from the beginning unless the user explicitly asks.

Completion checks:

- Metadata complete: `blogger_posts` row exists with valid title, metrics, and author guard passes.
- Media cache complete: local audio+video files exist at `output/media-cache/bilibili/bloggers/<mid>/<bvid>/` and are larger than 1KB.
- Comment pass complete: comments exist for the post in `blogger_posts.raw_payload.comment_capture` with `status: ok` and `requested_comment_limit >= 50`.
- Video understanding complete: `raw_payload.content_evidence.video_understanding.status` is `analyzed` with transcript and/or visual evidence.

For every resumed run, first query the next uncompleted posts from `blogger_posts` ordered by `published_at desc`, then process only those that are missing cache, comments, or video understanding.

## Rolling Workflow

### 1. Register/Find Blogger

First, find or register the blogger in the `bloggers` table. The blogger's `mid` (Bilibili user ID) is the primary identifier.

To find a blogger's mid from their name, use the Bilibili search API:
```
https://api.bilibili.com/x/web-interface/search/type?search_type=bili_user&keyword=<name>
```

Or navigate to their space page and extract the mid from the URL: `https://space.bilibili.com/<mid>`.

Register in `bloggers` table:
```
platform: 'bilibili'
platform_user_id: '<mid>'
handle: '<username>'
display_name: '<display name>'
profile_url: 'https://space.bilibili.com/<mid>'
```

### 2. Fetch WBI Signing Keys

Before calling space APIs, fetch the WBI signing keys:

```
GET https://api.bilibili.com/x/web-interface/nav
```

Extract `img_url` and `sub_url` from `data.wbi_img`, then compute the mixin key using the standard Bilibili WBI mixing table.

### 3. Fetch All Videos from Space

Use the space video search API with WBI signing:

```
https://api.bilibili.com/x/space/wbi/arc/search?mid=<mid>&ps=30&pn=<page>&order=pubdate&w_rid=<hash>&wts=<timestamp>
```

Paginate through all pages until `data.page.count` videos are collected or no more results. Process newest first (order=pubdate).

Environment variables:

```powershell
$env:BILIBILI_BLOGGER_MID='<mid>'
$env:BILIBILI_BLOGGER_MAX_VIDEOS='0'  # 0 = all
$env:BILIBILI_BLOGGER_SKIP_COMMENTS='0'
$env:BILIBILI_BLOGGER_COMMENT_LIMIT='50'
$env:BILIBILI_BLOGGER_DOWNLOAD_MEDIA='1'
$env:BILIBILI_BLOGGER_SKIP_ANALYSIS='0'
$env:BILIBILI_BLOGGER_DB_RESUME_ONLY='0'  # 1 = skip API, use DB only
# For analysis, point to main repo tools:
$env:FFMPEG_EXE='D:\media-coding\output\tools\ffmpeg\ffmpeg.exe'
$env:FFPROBE_EXE='D:\media-coding\output\tools\ffmpeg\ffprobe.exe'
$env:WHISPER_CPP_EXE='D:\media-coding\output\tools\whisper.cpp\Release\whisper-cli.exe'
$env:WHISPER_CPP_MODEL='D:\media-coding\output\tools\whisper.cpp\models\ggml-base.bin'
npm run scrape:bilibili-blogger
```

### 4. Per-Video Processing

For each video in the batch:

#### 4a. Metadata Collection

Fetch full video details:
```
GET https://api.bilibili.com/x/web-interface/view?bvid=<bvid>
```

Store in `blogger_posts`:
- `title`: video title
- `content`: video description (desc)
- `url`: `https://www.bilibili.com/video/<bvid>/`
- `published_at`: from pubdate timestamp
- `view_count`: stat.view
- `liked_count`: stat.like
- `comment_count`: stat.reply
- `collect_count`: stat.favorite
- `share_count`: stat.share
- `raw_payload.metrics.coin_count`: stat.coin
- `raw_payload.metrics.danmaku_count`: stat.danmaku

#### 4b. Comment Collection

Fetch top 50 comments via paginated API:
```
GET https://api.bilibili.com/x/v2/reply/main?type=1&oid=<aid>&mode=3&next=<cursor>
```

Store comments in `blogger_posts.raw_payload.top_comments` and write to `comments` table with `blogger_post_id`.

Record status in `raw_payload.comment_capture`:
- `status`: ok / no_comments / rate_limited / api_error
- `requested_limit`: 50
- `collected`: actual count
- `total_number`: from cursor.all_count

#### 4c. Video Media Caching

Cache to `output/media-cache/bilibili/bloggers/<mid>/<bvid>/`:
- `audio.m4s` - audio stream
- `video.m4s` - video stream

Use DASH playurl API:
```
GET https://api.bilibili.com/x/player/playurl?bvid=<bvid>&cid=<cid>&fnval=16&qn=64&fourk=0
```

Select mid-quality video and best-quality audio.

#### 4d. Video Understanding

Run after media caching. Pipeline:

1. Try Bilibili subtitle API first (`/x/player/v2`)
2. If no subtitles, transcribe cached audio with whisper.cpp
3. If whisper.cpp fails, fallback to OpenAI transcription
4. Extract scene key frames from cached video with ffmpeg
5. Analyze frames with Codex/Claude for visual timeline
6. Generate comprehensive content summary (no word limit)

Store in `raw_payload.content_evidence`:
- `video_content_summary`: full content summary in Chinese
- `audio_transcript`: complete transcript
- `audio_source`: subtitle/whisper.cpp/openai
- `visual_timeline`: frame-by-frame description
- `visual_frame_paths`: local frame file paths
- `video_understanding.status`: analyzed/missing_evidence/failed

### 5. Content Summary Requirements

The video content summary must be comprehensive with no word limit. Aim to completely represent what the video covers:
- Main topic and thesis
- All key arguments and evidence presented
- Specific data, examples, and case studies mentioned
- Narrative arc and transitions between segments
- Conclusions and takeaways
- Any calls to action or recommendations

Write in natural Chinese. Do not reference the UP主, platform, or analysis process.

### 6. WBI Signing Implementation

The WBI signing algorithm:

1. Fetch nav API to get `img_url` and `sub_url` (this API returns code -101 when not logged in but still includes wbi_img data — do NOT use `fetchBilibili` which throws on non-zero codes; use raw fetch)
2. Extract filenames (without extension) → `img_key` and `sub_key`
3. Concatenate `img_key + sub_key` to get raw key
4. Apply the standard Bilibili mixing table (64 indices) to reorder characters
5. Take first 32 characters as the `mixin_key`
6. Build params as a raw key-value object (NOT via URL constructor)
7. Add `wts` (current unix timestamp) to params
8. Sort all params by key
9. For each value: remove `!'()*` characters, then `encodeURIComponent(key)=encodeURIComponent(value)`
10. Join with `&` to form the query string
11. Append `mixin_key` to the query string
12. MD5 hash → `w_rid`
13. The final URL uses the same encoded query + `&w_rid=<hash>`

**Critical**: The MD5 hash MUST use URL-encoded values (via `encodeURIComponent`), not raw values. Using raw values produces -352 errors.

**Critical**: Do NOT parse the base URL with `new URL()` when params contain JSON values (like `dm_img_inter`). The URL constructor may mangle `{}[]` characters. Instead, pass params as a plain object to the signing function.

Cache the mixin key for up to 12 hours (keys rotate daily).

### 7. Cookie Requirements

Bilibili APIs require specific cookies to avoid HTTP 412 / -799 errors:

1. Get `buvid3` and `buvid4` from `https://api.bilibili.com/x/frontend/finger/spi`
2. If SPI fails, generate locally: buvid3 = `{MD5_HEX_UUID}infoc`, buvid4 = `{MD5_HEX_UUID}-{YYYYMMDDHHMMSS}-suffix`
3. Also generate: `b_nut` (unix timestamp), `_uuid` (UUID format + infoc), `buvid_fp` (MD5 of uuid + timestamp)
4. Optional: `SESSDATA` cookie from a logged-in browser session (set via `BILIBILI_SESSDATA` env var) enables more API access

### 8. Space API Anti-Fingerprint Parameters

The space video search API (`/x/space/wbi/arc/search`) requires additional anti-fingerprint params:
- `dm_img_list`: `[]`
- `dm_img_str`: `V2ViR0wgMS4w` (base64 of "WebGL 1.0")
- `dm_cover_img_str`: `V2ViR0wgMS4w`
- `dm_img_inter`: `{"ds":[],"wh":[0,0,0],"of":[0,0,0]}`

### 9. Fallback Strategy

The WBI-signed space API may still return -352 intermittently. The script falls back to the legacy endpoint (`/x/space/arc/search`) which works without WBI but may return -799 under rate limiting. Wait 30+ seconds between retries (escalating: 30s, 60s, 90s).

Three-tier fallback for video discovery:
1. **Space API (WBI + legacy)**: primary method, paginates through all videos
2. **Search API**: `search_type=video&keyword=<blogger_name>`, filters by mid, different rate limit pool
3. **DB resume**: loads existing `blogger_posts` records for incomplete processing

### 9a. CDN Download Strategy

Bilibili CDN actively closes connections after ~2MB of video data transfer. Direct downloads fail for video streams larger than ~2MB.

**Range download approach**: Use 1.5MB chunk size (under the 2MB CDN limit) with per-chunk retry (3 attempts, 1s/2s backoff). Each chunk gets a 30s timeout. For a 33MB video, this means ~22 range requests with 200ms inter-chunk delay.

Audio streams are typically unaffected by this CDN limit and download normally via direct transfer.

### 10. Comment API Behavior

Without login cookies, the reply API (`/x/v2/reply/main?mode=3`) may return only 3 "top hot" comments with `cursor.is_end: true`. The script tries both mode=3 (hot) and mode=0 (by time) to maximize collection. For full 50-comment coverage, consider providing `BILIBILI_SESSDATA`.

### 11. Rate Limiting And IP Bans

Bilibili aggressively rate-limits and temporarily bans IPs that make too many API calls:
- **-799 error**: API-level rate limiting. Wait 30-60 seconds between retries.
- **-412 error**: IP-level ban across all API endpoints (including search API). Wait 10-30 minutes.
- **HTTP 412**: Cookie/fingerprint rejection. Regenerate cookies.
- **ECONNRESET / TLS reset**: IP-level temporary ban (5-15 minutes). Stop all requests and wait.
- **Video detail API**: Can handle ~15-20 calls before rate limiting kicks in. Use 1.5-2s sleep between videos.
- **Space API**: Very sensitive. Only 1-2 pages can be fetched per session.
- **CDN (bilivideo.com)**: Separate from API rate limits. Media downloads work even when API is blocked.

Between runs, wait at least 10 minutes for rate limits to clear. Use `BILIBILI_BLOGGER_VIDEO_SLEEP_MS=2000` for conservative pacing.

### 12. Resume Mode

The script automatically resumes interrupted runs:
- Videos with existing metadata + cached media are skipped (checked via DB + local file existence)
- Space API failures trigger DB-driven resume using existing `blogger_posts` records
- Media downloads check for existing cached files before attempting download
- Each batch has a 3-second pause between transitions

## Implementation

Script: `src/server/scripts/scrape-bilibili-blogger.ts`
NPM command: `npm run scrape:bilibili-blogger`

Reuse from existing codebase:
- `db` client and `bloggers`/`bloggerPosts` schema from `src/server/db/`
- Comment normalization patterns from `scrape-bilibili-hotspots.ts`
- Video download and DASH patterns from `analyze-bilibili-hotspot-videos.ts`
- Subtitle, STT, frame extraction, and AI summary from `analyze-bilibili-hotspot-videos.ts`
- Media cache directory structure and serving from `src/server/routes/media-cache.ts`

## Validation

After capture, verify:
- `bloggers` row exists with correct `platform_user_id` and `platform='bilibili'`
- `blogger_posts` count matches expected video count from space API
- For each post: title, url, metrics, published_at are populated
- Comment capture status is recorded for each post
- Media cache files exist and are > 1KB
- Content evidence has transcript and/or visual timeline
- Video content summary is comprehensive (> 200 characters for videos > 1 minute)
