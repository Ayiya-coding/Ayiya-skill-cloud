---
name: douyin-cdp
description: Capture or implement Douyin Creator Center "Douyin Index" hotlist pipelines through logged-in ShadowBot Browser CDP. Use when Codex needs to scrape creator.douyin.com arithmetic-index data, Douyin real-time/rising hotlists, first-left popular videos, video metrics, AI audio/visual summaries, top comments, or database scripts for the media-coding project.
---

# Douyin CDP

## Core Rule

Treat the logged-in Douyin Creator Center page as the source of truth:

```text
https://creator.douyin.com/creator-micro/creator-count/arithmetic-index
```

Use ShadowBot Browser through CDP, preserve the user's login state, and never print or store cookie values. If Douyin asks for login, QR scan, CAPTCHA, SMS, or risk verification, stop and request human intervention.

## Capture Pipeline

1. Launch ShadowBot Browser with a temporary copied profile and `--remote-debugging-port`.
2. Navigate to the Creator Center arithmetic index page.
3. Record network responses and page state for both hotlists:
   - `douyin_realtime_hotspots`: "抖音实时热点", 30 rows.
   - `douyin_rising_hotspots`: "抖音飙升热点", 30 rows.
4. Prefer authenticated JSON responses over DOM parsing. Use DOM parsing only as a fallback and record `selection_source`.
5. For each row, store rank, hotspot name, hotspot index, and index change.
6. Open the topic detail. In "热门内容", select the visually leftmost video card exactly as shown on the page; do not replace it with another video even if another video has higher comments.
7. Capture the selected video's publish time, caption, like/comment/collect/share counts, detail URL, and top 50 comments.
8. Summarize video audio and visuals with AI when available:
   - Prefer reliable platform transcript/OCR/frame-summary fields if the authenticated payload exposes them.
   - Otherwise use Claude CLI or Codex CLI on downloaded video/audio/frames when configured.
   - If neither can inspect media, write limitations clearly instead of inventing audio or visual content.
9. Keep historical snapshots. Do not overwrite old captures; every run gets a `capture_batch_id` and `captured_at`.

## media-coding Contract

For `D:\media-coding`, implement or maintain:

- Script: `src/server/scripts/scrape-douyin-creator-index.ts`
- Command: `npm run scrape:douyin-creator-index`
- Post-capture video understanding script: `src/server/scripts/analyze-douyin-creator-videos.ts`
- Post-capture command: `npm run analyze:douyin-creator-videos`
- Tables:
  - `douyin_realtime_hotspots`
  - `douyin_rising_hotspots`
- Optional environment variables:
  - `DOUYIN_CREATOR_LIMIT=30`
  - `DOUYIN_CREATOR_EXPECTED_HOTLIST_ROWS=30`
  - `DOUYIN_CREATOR_STRICT_HOTLIST_ROWS=1` by default; set `0` only for explicit partial diagnostics.
  - `DOUYIN_CREATOR_COMMENT_LIMIT=50`
  - `DOUYIN_CREATOR_PACE_MIN_MS=1200`
  - `DOUYIN_CREATOR_PACE_JITTER_MS=1800`
  - `DOUYIN_CREATOR_STAGE_COOLDOWN_MS=5000`
  - `DOUYIN_CREATOR_KEEP_PROFILE=1`
  - `DOUYIN_AI_ANALYZER=claude|codex|none`
  - `DOUYIN_CREATOR_CAPTURE_VIDEO_PAGE=1|0`
  - `DOUYIN_CREATOR_CAPTURE_FRAMES=1|0`
  - `DOUYIN_CREATOR_FRAME_COUNT=8`
  - `DOUYIN_CREATOR_DOWNLOAD_MEDIA=1|0`
  - `DOUYIN_CREATOR_COMMENTS_ONLY_BATCH=<capture_batch_id>` to reopen existing video pages and update only `top_comments` plus comment-refresh evidence without creating a new hotlist batch or overwriting AI summaries.
  - `DOUYIN_CREATOR_COMMENTS_ONLY_SCOPE=missing|all`; default `missing` refreshes empty, short, failed, or suspicious comment rows only.
  - `DOUYIN_CREATOR_ANALYZE_BATCH=<capture_batch_id>` to re-analyze an existing batch's selected videos.
  - `DOUYIN_CREATOR_ANALYZE_KINDS=realtime,rising`
  - `DOUYIN_VIDEO_ANALYSIS_LIMIT=60`
  - `DOUYIN_VIDEO_ANALYSIS_FORCE=1` to overwrite an existing `content_evidence.video_content_summary`.
  - `DOUYIN_VIDEO_ANALYSIS_DRY_RUN=1` to test the workflow without writing the database.
  - `DOUYIN_VIDEO_REQUIRE_AUDIO_TRANSCRIPT=0` only when visual-only summaries are acceptable.
  - `DOUYIN_VIDEO_REQUIRE_VISUAL_EVIDENCE=0` only when audio/caption-only summaries are acceptable.
  - `DOUYIN_STT_ENGINE=auto|whisper.cpp|whisper-python|openai|none`
  - `WHISPER_CPP_EXE` and `WHISPER_CPP_MODEL`
  - `FFMPEG_EXE`
  - `OPENAI_API_KEY` and `OPENAI_TRANSCRIBE_MODEL=gpt-4o-transcribe` for the cloud transcription fallback.
  - `DOUYIN_VIDEO_KEEP_TEMP=1` to preserve temp media/audio/frames for debugging.
  - `CLAUDE_CLI_EXE` or `CODEX_CLI_EXE`
  - `SHADOWBOT_BROWSER_EXE`
  - `SHADOWBOT_USER_DATA_DIR`

Expected row fields include rank, hotspot name/index/change, detail URL, selected video publish time/caption/content summaries/counts/detail URL, top comments JSON, content evidence JSON, raw payload JSON, capture status, and error message.

For exact schema and validation details, read [references/douyin-creator-index-pipeline.md](references/douyin-creator-index-pipeline.md).

For the `D:\media-coding` machine, project-local defaults may exist under:

- `output/tools/ffmpeg/ffmpeg.exe`
- `output/tools/ffmpeg/ffprobe.exe`
- `output/tools/whisper.cpp/Release/whisper-cli.exe`
- `output/tools/whisper.cpp/models/ggml-base.bin`

## Video Understanding Workflow

Use a two-stage model for "what did this video say and show?":

1. Evidence acquisition:
   - Audio evidence first becomes text through STT. Prefer platform ASR/subtitle fields, then local `whisper.cpp`, then Python `openai-whisper`, then OpenAI Transcriptions API if configured.
   - Codex CLI and Claude Code CLI should be treated as reasoning/summarization tools, not as the stable raw-audio transcription layer. Current local CLI help exposes Codex image input and Claude text/stream print mode, but no stable direct local audio-file input.
   - Visual evidence should come from key frames. Prefer scene-change frames with `ffmpeg select='gt(scene,...)'`; if that fails, use evenly timed fallback frames or CDP video screenshots.
2. AI synthesis:
   - Feed transcript, visual timeline, publish caption, topic name, and known limitations to Codex/Claude.
   - Store the final one-paragraph Chinese summary in `content_evidence.video_content_summary`.
   - By default, require an audio transcript before writing `content_evidence.video_content_summary`; otherwise keep the row as `missing_evidence` so the UI does not show a visual-only guess as complete understanding.
   - By default, require visual evidence before writing `content_evidence.video_content_summary`; otherwise keep the row as `missing_evidence`. Use `DOUYIN_VIDEO_REQUIRE_VISUAL_EVIDENCE=0` only for explicit audio-only diagnostics.
   - The summary must be natural text under 800 Chinese characters. It should cover: what event the video is about, what appears on screen, who the main subject is, what scene they are in, what they do, and what the video is trying to express.
   - Do not put tool failure text such as "cannot directly hear audio" into the user-facing summary. Record that only under `content_evidence.video_understanding.limitations`.
3. Temp-file policy:
   - Put downloaded videos, extracted audio, and frames under `output/douyin-video-analysis-temp/`.
   - Delete each row's temp directory after analysis unless `DOUYIN_VIDEO_KEEP_TEMP=1`.
   - Also clean old temp dirs by `DOUYIN_VIDEO_TEMP_RETENTION_HOURS` (default 6).

If a saved Douyin CDN video URL returns 403, tiny HTML, or an expired timestamp response, treat it as expired. Reopen the video detail page in the logged-in browser and refresh playable media evidence from `video.currentSrc` or network responses before retrying STT.

## Field Notes

When repeating this capture, handle these known Douyin Creator Center behaviors:

- Run the workflow as low-frequency staged capture, not a single dense burst. Use stage cooldowns, jittered pauses, and failure-only retries. Reopening every video or every comment page repeatedly is higher risk and should be avoided unless explicitly diagnosing.
- Login, QR scan, SMS, CAPTCHA, or risk verification must be handed to the user. Reuse the logged-in ShadowBot profile after the user finishes.
- The Creator Center upgrade notice can cover the hotlists. Click the smallest visible confirm/known button, then wait again.
- Sometimes one or both hotlists render as empty. Wait briefly and retry the index page once before declaring no data.
- The page can remember a hotlist/page state. Before reading each list, click that list label and page 1, then collect pages 2 and 3.
- Do not fabricate full pages when pagination fails. The rising list has 30 records across pages; if the script sees only 10 unique DOM rows, treat the hotlist as incomplete and stop before detail capture unless `DOUYIN_CREATOR_STRICT_HOTLIST_ROWS=0` is explicitly set for diagnostics.
- For rising pagination, clicking page 2/3 must be verified by row-name changes and unique accumulated rows. If page 2/3 adds no new hotspot names, try the section-scoped next-page control and section scroll. If still below 30, fail fast with `hotlist_incomplete`.
- Pagination page numbers can be confused with rank numbers inside the hotlist, and realtime/rising tables can sit side by side with separate pagers. When clicking page 2/3, prefer elements whose own or parent class/aria/title contains `page`, `pagination`, `pager`, `semi-page`, `byted-pager`, or `ant-pagination`, and require the pager element to be inside the same horizontal card range as the target hotlist label. Verify new hotspot names were added after the click.
- Hotlist API discovery is not reliable enough by itself. Keep DOM pagination fallback as the primary safety net, and select the smallest visible tab/label element when paging realtime/rising lists.
- Some hotlist API responses return encrypted `data` strings even in logged-in sessions. Treat them as audit evidence unless the page's own JS API returns decoded rows; do not parse encrypted blobs as final data.
- Topic detail pages lazy-load "热门内容". Scroll that label into view before collecting cards.
- Select the visually leftmost card only. Ignore left navigation and unrelated panels by requiring candidates to be inside the hot-content area and right of the app sidebar.
- Do not treat topic-detail "评论量 TOP5" or card metrics as real video comments. Real `top_comments` come only from the opened `www.douyin.com/share/video/...` or `/video/...` page, preferably comment API payloads.
- Do not treat broad DOM nodes as real comments. If extracted "comments" start with navigation or recommendation text such as `通知`, `私信`, `播放中`, `TA的作品`, or related-video titles, discard them and leave `top_comments` empty or retry with network comment payloads.
- When a previous run already saved fake DOM comments, first clear those `top_comments` for the affected batch, then rerun with `DOUYIN_CREATOR_COMMENTS_ONLY_BATCH=<capture_batch_id>`. This preserves the historical hotlist/AI snapshot while correcting only the comment field.
- For comment extraction, prefer comment/reply network payloads over DOM text. Use DOM only as a last fallback, and filter UI/navigation strings such as `通知`, `私信`, `不开启`, `播放中`, `相关推荐`, `TA的作品`, `客户端下载`, `全部评论`, and `热门评论`.
- If the comment API returns only the first page (often 5-10 comments) while the opened video page has more clean comment DOM rows after scrolling, keep the network comments first and append filtered DOM comments until `DOUYIN_CREATOR_COMMENT_LIMIT` is reached. Re-validate with a UI-string scan before trusting the merged list.
- Do not trust `top_comments.length === 50` by itself. After comments-only refresh, run a quality scan for UI strings such as `分享 回复`, `展开N条回复`, and plain reply/share counters. If present, clean and re-rank `top_comments`; fewer real comments are better than 50 entries polluted by buttons.
- Video detail pages can redirect to `/jingxuan?modal_id=...`; footer ICP/license numbers can be misread as collect/share counts. Prefer compact count lines near the playback controls and drop values outside PostgreSQL integer range.
- Some topics have no visible popular video. Save the row as `partial` with a clear error instead of inventing a video.
- For AI audio/visual summaries, record whether the analyzer inspected a platform transcript, media URL, or local media file. If the CLI only saw text evidence, preserve that limitation.
- Frame capture must not depend on `DOUYIN_AI_ANALYZER`. If `DOUYIN_CREATOR_CAPTURE_FRAMES=1`, capture browser screenshots even when AI summarization is disabled during the scrape stage.
- For visual summaries with Codex CLI, prefer media-derived scene frames from `analyze:douyin-creator-videos`; if media download fails, use browser screenshot frames captured during the scrape stage.
- Audio recognition depends on platform ASR/subtitle fields or a local media/STT toolchain. If neither exists, keep `audio_summary` empty/null and write the limitation.
- In the 2026-05-05 full run, strict video understanding completed 43/60 rows. The remaining rows mostly had no usable Whisper transcript, aborted/failed media download, or one Codex visual timeout. In strict mode, keep those rows as `missing_evidence`; do not downgrade to visual-only summaries unless the user explicitly accepts `DOUYIN_VIDEO_REQUIRE_AUDIO_TRANSCRIPT=0`.
- If several unrelated hotspots resolve to the same video id `1864265008027784` with empty comments and missing collect/share counts, treat it as a suspicious placeholder/detail-selection failure in the next run. Reopen the topic detail and reselect the leftmost hot-content card instead of trusting that duplicate URL.
- If one row has a Codex visual timeout but already has frame paths, retry only that batch/row with a higher `DOUYIN_VIDEO_ANALYZER_TIMEOUT_MS` or rerun the batch without `DOUYIN_VIDEO_ANALYSIS_FORCE` so completed rows are skipped and only missing-evidence rows are retried.
- On this machine, a dry-run found historical Douyin CDN media URLs returning HTTP 403 with only 238 bytes while still reporting `content-type=video/mp4`. Treat this as expired media evidence, not a real video file. Reopen the video page and refresh playable media before STT.
- Existing `content_evidence` can contain nested `video_page_evidence` from earlier merge runs. Cap recursive media URL extraction depth to avoid stack overflows.
- Project-local `ffmpeg`, `ffprobe`, `whisper.cpp`, and `ggml-base.bin` may be installed under `output/tools/`; prefer these before asking the user to install global tools.

## Validation Checklist

After a full run, verify:

- 30 realtime rows and 30 rising rows were saved for the latest `capture_batch_id`, unless Douyin returned fewer and the run explains why.
- Ranks are unique within each table and batch.
- Each captured row records whether it came from API, DOM, or fallback.
- The selected video is the leftmost "热门内容" card on the detail page.
- `top_comments` contains up to 50 comments in platform display order.
- AI media summaries include evidence and limitations.
- Cookie values are absent from logs, JSON output, and database rows.
- Temporary ShadowBot runtime profiles under `output/` are removed unless explicitly preserved.
