---
name: bilibili-cdp
description: Capture, implement, or debug Bilibili daily popular, ranking, search-trend, video-detail, metric, and comment pipelines for the media-coding project. Use when Codex needs to refresh B站 综合热门, 排行榜-全部, 热搜排行榜, or explicitly run the one-time 入站必刷 backfill.
---

# Bilibili CDP

## Core Rule

Treat Bilibili's own web JSON endpoints as the first source of truth. Use page URLs as the user-facing entry points, but collect the structured data from the API responses behind those pages.

Default daily mode is only:

1. 综合热门: fetch `https://api.bilibili.com/x/web-interface/popular?ps=<page_size>&pn=<page>`.
2. 排行榜-全部: fetch `https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all`.
3. 热搜排行榜: fetch `https://api.bilibili.com/x/web-interface/wbi/search/square?limit=50&platform=web`.

入站必刷 is a one-time backfill. Do not include it in daily runs unless the user explicitly asks to initialize, backfill, refresh, or rerun 入站必刷.

Use this shared pipeline:

4. For explicit 入站必刷 backfills, fetch `https://api.bilibili.com/x/web-interface/popular/precious?page_size=<n>&page=1`.
5. For video rows, confirm detail and current stats with `https://api.bilibili.com/x/web-interface/view?aid=<aid>` or `?bvid=<bvid>`.
6. For video rows, fetch comments through `https://api.bilibili.com/x/v2/reply/main?type=1&oid=<aid>&mode=3&next=<cursor>`.
7. Store every collected video/list/search row in `hotspots`, and store video comments in both the `comments` table and `raw_payload.top_comments`.
8. Preserve source category in `hotspots.category`:
   - `bilibili_popular_all`
   - `bilibili_rank_all`
   - `bilibili_history`
   - `bilibili_search_square`
9. Do not claim complete comments unless pagination really reached `is_end=true`. Daily 综合热门 and 排行榜-全部 must collect the first 50 top-level comments for every video by default; if a run stops because of this configured limit, record the cap in `raw_payload.comment_fetch`.
10. If the comment API returns `Bilibili API -352`, treat it as a rate-limit / anti-bot signal. Stop or skip comment fetching instead of retrying tightly.
11. For daily main-data refreshes, do not set `BILIBILI_SKIP_COMMENTS=1`. Use `BILIBILI_COMMENT_LIMIT=50` and a multi-second `BILIBILI_VIDEO_SLEEP_MS`. Use `BILIBILI_SKIP_COMMENTS=1` only as an explicit emergency fallback after a real anti-bot signal.
12. For "内容简介" quality, run the post-capture video-understanding workflow. It must cache the Bilibili media locally, acquire audio transcript and visual key-frame evidence, then write a pure audio+visual summary to `raw_payload.content_evidence.video_content_summary`.

## media-coding Contract

For `D:\media-coding`, implement or maintain:

- Script: `src/server/scripts/scrape-bilibili-hotspots.ts`
- Command: `npm run scrape:bilibili-hotspots`
- Post-capture video understanding script: `src/server/scripts/analyze-bilibili-hotspot-videos.ts`
- Post-capture command: `npm run analyze:bilibili-hotspot-videos`
- Platform value: `bilibili`
- UI: replace the legacy 小红书 hotspot tab with B站 and add second-level tabs.
- API verification examples:
  - `GET http://127.0.0.1:8787/api/hotspots?platform=bilibili&category=bilibili_popular_all&status=active&limit=100&sort=rank&direction=asc&include_raw=true`
  - `GET http://127.0.0.1:8787/api/hotspots?platform=bilibili&category=bilibili_rank_all&status=active&limit=100&sort=rank&direction=asc&include_raw=true`
  - `GET http://127.0.0.1:8787/api/hotspots?platform=bilibili&category=bilibili_search_square&status=active&limit=50&sort=score&direction=desc&include_raw=true`

Useful environment variables:

- `BILIBILI_KINDS=popular_all,rank_all,search_square`; daily default when omitted
- `BILIBILI_KINDS=history`; one-time 入站必刷 backfill only when explicitly requested
- `BILIBILI_KINDS=all`; explicit four-category maintenance run
- `BILIBILI_POPULAR_LIMIT=20`
- `BILIBILI_RANK_LIMIT=100`
- `BILIBILI_HISTORY_LIMIT=100`
- `BILIBILI_SEARCH_LIMIT=50`
- `BILIBILI_COMMENT_LIMIT=50`; daily default for 综合热门 and 排行榜-全部
- `BILIBILI_SKIP_COMMENTS=1`; emergency fallback only after comment anti-bot signals, not the daily default
- `BILIBILI_COMMENT_PAGE_SLEEP_MS=350`
- `BILIBILI_VIDEO_SLEEP_MS=500`
- `BILIBILI_VIDEO_ANALYSIS_LIMIT=5`; set `0` to process all pending unique Bilibili videos in the selected categories
- `BILIBILI_VIDEO_ANALYSIS_FORCE=1` to overwrite an existing `content_evidence.video_content_summary`
- `BILIBILI_VIDEO_ANALYSIS_DRY_RUN=1`
- `BILIBILI_VIDEO_ANALYSIS_CATEGORIES=bilibili_popular_all,bilibili_rank_all`; daily default when omitted
- `BILIBILI_VIDEO_ANALYSIS_CATEGORIES=bilibili_history`; explicit 入站必刷 video-understanding backfill
- `BILIBILI_VIDEO_ANALYSIS_SLEEP_MS=1800`
- `BILIBILI_VIDEO_REQUIRE_AUDIO_TRANSCRIPT=0` only when visual-only summaries are acceptable
- `BILIBILI_VIDEO_REQUIRE_VISUAL_EVIDENCE=0` only when audio/caption-only summaries are acceptable
- `BILIBILI_STT_ENGINE=auto|whisper.cpp|whisper-python|openai|none`
- `BILIBILI_VIDEO_SUMMARY_ANALYZER=auto|claude|codex|none`; `auto` prefers Codex first because this machine already uses Codex image input for key-frame evidence.
- `BILIBILI_VIDEO_KEEP_TEMP=1`
- `BILIBILI_VIDEO_RANGE_CHUNK_BYTES=4000000` for the fallback chunk size when a Bilibili media CDN terminates whole-file downloads.
- `FFMPEG_EXE`, `WHISPER_CPP_EXE`, `WHISPER_CPP_MODEL`, `OPENAI_API_KEY`, `CLAUDE_CLI_EXE`, `CODEX_CLI_EXE`

Safe daily video-understanding pattern:

```powershell
$env:BILIBILI_VIDEO_ANALYSIS_LIMIT='0'
$env:BILIBILI_VIDEO_ANALYSIS_CATEGORIES='bilibili_popular_all,bilibili_rank_all'
$env:BILIBILI_VIDEO_ANALYSIS_SLEEP_MS='3000'
$env:BILIBILI_VIDEO_SUMMARY_ANALYZER='codex'
npm run analyze:bilibili-hotspot-videos
```

The video-understanding run is resumable. It skips videos that already have a quality-valid `raw_payload.content_evidence.video_content_summary`; old summaries that mention metadata, analysis process, uncertainty language, or backend failures are treated as pending. Use `BILIBILI_VIDEO_ANALYSIS_FORCE=1` only when intentionally replacing valid summaries. Do not run multiple full analyzers at the same time. This stage can take hours because each unique video may need media download, local STT, frame extraction, image analysis, and text synthesis.

By default, video understanding only processes daily video categories: 综合热门 and 排行榜 all. Use `BILIBILI_VIDEO_ANALYSIS_CATEGORIES=bilibili_history` only when explicitly completing the one-time 入站必刷 backfill.

Safe daily main refresh pattern:

```powershell
$env:BILIBILI_KINDS='popular_all,rank_all,search_square'
$env:BILIBILI_POPULAR_LIMIT='100'
$env:BILIBILI_RANK_LIMIT='100'
$env:BILIBILI_SEARCH_LIMIT='50'
$env:BILIBILI_COMMENT_LIMIT='50'
$env:BILIBILI_VIDEO_SLEEP_MS='3000'
npm run scrape:bilibili-hotspots
```

One-time 入站必刷 backfill pattern:

```powershell
$env:BILIBILI_KINDS='history'
$env:BILIBILI_HISTORY_LIMIT='100'
$env:BILIBILI_SKIP_COMMENTS='1'
$env:BILIBILI_VIDEO_SLEEP_MS='3000'
npm run scrape:bilibili-hotspots
```

Expected video `hotspots.raw_payload` shape:

- `capture`: captured_at, source_kind, source_url, requested_comment_limit, comment_exhausted
- `video`: aid, bvid, title, url, cover_url, owner, published_at, publish_text, description, category names
- `metrics`: view_count, danmaku_count, comment_count, like_count, coin_count, collect_count, share_count
- `rank`: source_rank, rank_score when present
- `top_comments`: the collected first 50 top-level comments by default
- `comment_fetch`: requested_limit, collected, exhausted, cursor, failures. When comments are intentionally skipped, `requested_limit` is `skipped` and `failures` includes `comment_fetch_skipped`.
- `content_evidence`: video_content_summary, audio_transcript, visual_timeline, video_understanding status and limitations
- `media_cache`: cached Bilibili audio/video files under `output/media-cache/bilibili/`
- `raw`: source row and detail response excerpts

After video understanding, keep `hotspots.description` as the platform text. The legacy detail drawer must use `raw_payload.content_evidence.video_content_summary` as 内容简介. The raw evidence remains the source of truth under `raw_payload.content_evidence`.

## Video Understanding Workflow

Use the same evidence discipline as `douyin-cdp`:

1. Group current Bilibili rows by `aid`/`bvid` so the same video appearing in multiple tabs is analyzed once, then synced back to every row.
2. Evidence acquisition:
   - Try Bilibili player subtitles first.
   - If no subtitle exists, download DASH audio from `/x/player/playurl` and transcribe through local `whisper.cpp`, Python Whisper, or OpenAI Transcriptions when configured.
   - Cache Bilibili DASH audio/video under `output/media-cache/bilibili/<aid>-cid-<cid>/` and reuse it on reruns.
   - Download a readable mid-bandwidth DASH video stream for key-frame extraction. Use `ffmpeg` scene frames first, then time-based fallback frames.
3. Visual understanding:
   - Use Codex CLI image input to summarize the key frames into `visual_timeline`.
   - The visual prompt must only receive frames. Do not feed it title, UP name, publish text, or platform description.
4. Final synthesis:
   - Feed only audio transcript and visual timeline into Codex/Claude.
   - Store the user-facing one-paragraph Chinese summary in `raw_payload.content_evidence.video_content_summary`.
   - The visible summary must directly say what happens in the audio and picture. It must not mention UP主, 博主, 作者, title, publish text, platform description, links, B站, analysis process, "音频转写", "画面显示", "根据证据", uncertainty language, or backend failure.
   - If the analyzer times out, returns empty output, or fails the visible-quality gate, leave the visible summary blank and record the reason under `video_understanding.limitations`; do not write a low-quality fallback into 内容简介.
   - Do not put backend failure text in the visible summary; keep it under `video_understanding.limitations`.
5. UI contract:
   - Bilibili detail drawers must prefer `raw_payload.content_evidence.video_content_summary` for 内容简介.
   - By default, require both audio transcript and visual evidence before writing the final summary.
6. Windows temp-file rule:
   - Keep media-analysis temp directory names ASCII-only, such as `aid-123-row-456`; emoji or Chinese video titles can make ffmpeg/whisper.cpp fail to reopen generated files.
7. Bilibili CDN download rule:
   - Whole-file DASH downloads can terminate mid-body even when the URL is valid. Retry the direct download, then fall back to HTTP Range chunks before marking media as unusable.
8. Resume and audit rule:
   - Audit files are written under `output/bilibili-video-analysis-audit/`.
   - Temp media and frames live under `output/bilibili-video-analysis-temp/` and should be deleted after each row unless `BILIBILI_VIDEO_KEEP_TEMP=1`.
   - A row with `video_understanding.status=missing_evidence` must not be treated as fully understood. It needs a retry or explicit diagnostic relaxation of the audio/visual requirement.

Expected search `hotspots.raw_payload` shape:

- `capture`: captured_at, source_kind, source_url
- `search_trend`: keyword, show_name, heat_score, icon, uri, goto

## Validation Checklist

After a daily scrape, verify:

- 综合热门 / 排行榜 all rows have title, URL, publish time, metrics, and comments metadata.
- 综合热门 / 排行榜 all rows collect `raw_payload.comment_fetch.requested_limit=50`; `collected` should be 50 unless the API exposed fewer comments or hit a recorded anti-bot failure.
- 热搜排行榜 rows sort by numeric `score` descending.
- `raw_payload.top_comments.length` matches saved comment rows for video categories.
- `raw_payload.comment_fetch.exhausted=false` is explained by `requested_limit`; `requested_limit=skipped` is valid only when `BILIBILI_SKIP_COMMENTS=1`.
- For video understanding, representative rows expose `raw_payload.content_evidence.video_content_summary`, `audio_transcript`, `visual_timeline`, and `video_understanding.status=analyzed`.
- The legacy hotspot UI loads B站 second-level tabs without breaking 抖音/微博/百度 tabs.
- Run `npm test -- src/tests/app-html-legacy-entry.test.ts src/tests/hotspot-platform-tabs.test.ts`.
- Run `npm run typecheck`.

After an explicit 入站必刷 backfill, also verify `bilibili_history` rows through `/api/hotspots`. Do not rerun 入站必刷 as part of normal daily refreshes.

For detailed field mapping, read [references/bilibili-hotspot-pipeline.md](references/bilibili-hotspot-pipeline.md).
