# Bilibili Hotspot Pipeline

## Categories

| UI tab | category | source |
| --- | --- | --- |
| 综合热门 | `bilibili_popular_all` | `https://www.bilibili.com/v/popular/all` via `/x/web-interface/popular` |
| 排行榜 all | `bilibili_rank_all` | `https://www.bilibili.com/v/popular/rank/all` via `/x/web-interface/ranking/v2?rid=0&type=all` |
| 入站必刷 | `bilibili_history` | `https://www.bilibili.com/v/popular/history` via `/x/web-interface/popular/precious` |
| 热搜排行榜 | `bilibili_search_square` | `/x/web-interface/wbi/search/square?limit=50&platform=web` |

## Field Mapping

Video rows:

- `hotspots.title` = video title
- `hotspots.description` = `dynamic || desc || achievement`; do not overwrite it during video understanding. The UI should prefer `raw_payload.content_evidence.video_content_summary` for 内容简介.
- `hotspots.url` = `https://www.bilibili.com/video/<bvid>/`
- `hotspots.rank` = source list order
- `hotspots.score` = source score or view count
- `hotspots.heat_text` = formatted play count for video tabs
- `raw_payload.video.publish_text` = `dynamic`, falling back to `desc`
- `raw_payload.video.description` = `desc` or `achievement`
- `raw_payload.metrics.comment_count` = Bilibili `stat.reply`, not collected comment sample length

Search rows:

- `hotspots.title` = `show_name || keyword`
- `hotspots.rank` = order in API list
- `hotspots.score` = `heat_score`
- `hotspots.heat_text` = formatted heat score

## Comment Notes

Bilibili's comment API can expose many pages. Daily 综合热门 and 排行榜 all runs must use `BILIBILI_COMMENT_LIMIT=50` and collect the first 50 top-level comments for every video. A limit of `0` means keep paging until the API reports the end, but this can be very slow for high-traffic videos.

If the comment API returns `Bilibili API -352`, treat it as a rate-limit / anti-bot signal. Do not keep retrying comment pages. Preserve the video row and record the failure in `raw_payload.comment_fetch.failures`.

For the daily main-data refresh, collect the first 50 comments for video tabs and slow down video requests. Daily means 综合热门, 排行榜 all, and 热搜排行榜:

```powershell
$env:BILIBILI_KINDS='popular_all,rank_all,search_square'
$env:BILIBILI_POPULAR_LIMIT='100'
$env:BILIBILI_RANK_LIMIT='100'
$env:BILIBILI_SEARCH_LIMIT='50'
$env:BILIBILI_COMMENT_LIMIT='50'
$env:BILIBILI_VIDEO_SLEEP_MS='3000'
npm run scrape:bilibili-hotspots
```

In this mode, video rows keep the platform metric `raw_payload.metrics.comment_count`, and save the collected comments in both `comments` and `raw_payload.top_comments`. `BILIBILI_SKIP_COMMENTS=1` is reserved for explicit anti-bot recovery runs.

Run 入站必刷 only as an explicit one-time backfill:

```powershell
$env:BILIBILI_KINDS='history'
$env:BILIBILI_HISTORY_LIMIT='100'
$env:BILIBILI_SKIP_COMMENTS='1'
$env:BILIBILI_VIDEO_SLEEP_MS='3000'
npm run scrape:bilibili-hotspots
```

Validated on 2026-05-05: the four-category maintenance run saved 100 综合热门 rows, 100 排行榜 all rows, 98 入站必刷 rows, and 50 热搜排行榜 rows. The daily default after that should not include 入站必刷.

Use `platform_comment_id = bilibili:<kind>:<aid>:<rpid>` so the same video can appear in multiple Bilibili tabs without comments moving between hotspot rows.

## Video Understanding Notes

Run video understanding after daily video lists have been saved:

```powershell
$env:BILIBILI_VIDEO_ANALYSIS_LIMIT='0'
$env:BILIBILI_VIDEO_ANALYSIS_CATEGORIES='bilibili_popular_all,bilibili_rank_all'
$env:BILIBILI_VIDEO_ANALYSIS_SLEEP_MS='3000'
$env:BILIBILI_VIDEO_SUMMARY_ANALYZER='codex'
npm run analyze:bilibili-hotspot-videos
```

The script processes unique videos, not rows. Current list rows can duplicate the same `aid` across 综合热门 and 排行榜 all; analyze once and update every matching row.

The run is resumable: existing quality-valid `raw_payload.content_evidence.video_content_summary` rows are skipped unless `BILIBILI_VIDEO_ANALYSIS_FORCE=1` is set. Old summaries that mention metadata, process language, uncertainty, or backend failures should be treated as pending. Do not run multiple full analyzers at once.

By default, the analyzer processes daily video categories only: `bilibili_popular_all` and `bilibili_rank_all`. Set `BILIBILI_VIDEO_ANALYSIS_CATEGORIES=bilibili_history` only when explicitly finishing the one-time 入站必刷 backfill.

Evidence order:

1. Bilibili subtitles from `/x/player/v2`.
2. DASH audio from `/x/player/playurl`, transcribed with local `whisper.cpp`, Python Whisper, or OpenAI Transcriptions.
3. DASH audio/video cache under `output/media-cache/bilibili/<aid>-cid-<cid>/`; reruns should reuse cached files before downloading.
4. DASH video key frames from `/x/player/playurl`, summarized through Codex image input. The visual prompt must not include title, UP name, publish text, or platform description.
5. Codex/Claude text synthesis into `raw_payload.content_evidence.video_content_summary` from only audio transcript plus visual timeline. If the analyzer fails or the summary contains metadata/process/uncertainty language, leave the visible summary blank and record the failure under `video_understanding.limitations`.

By default, do not write a final user-facing summary unless both audio transcript and visual evidence exist. If a diagnostic run intentionally allows weaker evidence, use `BILIBILI_VIDEO_REQUIRE_AUDIO_TRANSCRIPT=0` or `BILIBILI_VIDEO_REQUIRE_VISUAL_EVIDENCE=0` and record the limitation.

On Windows, keep analysis temp directory names ASCII-only, for example `aid-123-row-456`. Emoji or Chinese titles in paths can make ffmpeg or whisper.cpp fail to reopen generated audio files.

Bilibili CDN media URLs may return valid headers but terminate during whole-file body reads. Retry direct download first, then use HTTP Range chunks before treating the video as missing playable media. Successful downloads are durable cache, not disposable temp files.

Audit files are written to `output/bilibili-video-analysis-audit/`. Temp files are written to `output/bilibili-video-analysis-temp/` and should be deleted automatically unless `BILIBILI_VIDEO_KEEP_TEMP=1`.

Validation target: representative video rows should have `raw_payload.content_evidence.video_content_summary`, `audio_transcript`, `visual_timeline`, and `video_understanding.status=analyzed`. Rows marked `missing_evidence` are intentionally not fully summarized.
