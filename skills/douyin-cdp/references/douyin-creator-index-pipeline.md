# Douyin Creator Index CDP Pipeline

## Source Of Truth

Use the logged-in Creator Center page:

```text
https://creator.douyin.com/creator-micro/creator-count/arithmetic-index
```

The target data is not the public `www.douyin.com/hot` list. It is the Creator Center "抖音指数" page and its authenticated API responses.

## ShadowBot Runtime

Default executable:

```text
D:\Program Files (x86)\ShadowBot\ShadowBot Browser\Application\ShadowBotBrowser.exe
```

Default profile:

```text
%LOCALAPPDATA%\ShadowBotBrowser\User Data
```

Copy only the minimal profile files into a temp runtime profile before launching CDP:

- `Local State`
- `Default/Preferences`
- `Default/Secure Preferences`
- `Default/Network/Cookies`

Launch with:

```text
--user-data-dir=<temp-profile>
--profile-directory=Default
--remote-debugging-port=<open-port>
--no-first-run
--no-default-browser-check
```

Do not log cookie values. It is safe to log cookie names, cookie count, login-check status, and whether manual login is required.

## Data Model

Create two historical snapshot tables with the same shape:

- `douyin_realtime_hotspots`
- `douyin_rising_hotspots`

Recommended columns:

- `id`
- `capture_batch_id`
- `captured_at`
- `rank`
- `hotspot_name`
- `hotspot_index`
- `hotspot_index_text`
- `hotspot_index_change`
- `hotspot_index_change_value`
- `detail_url`
- `video_id`
- `video_published_at`
- `video_caption`
- `video_audio_summary`
- `video_visual_summary`
- `video_like_count`
- `video_comment_count`
- `video_collect_count`
- `video_share_count`
- `video_detail_url`
- `top_comments` as JSONB
- `content_evidence` as JSONB
- `raw_payload` as JSONB
- `capture_status`
- `error_message`
- `created_at`
- `updated_at`

Keep every run as history. Enforce uniqueness on `(capture_batch_id, rank)` per table, not on hotspot name.

## Network Capture Strategy

1. Enable CDP `Network.enable`, `Page.enable`, and `Runtime.enable`.
2. Navigate to the arithmetic index page.
3. Capture JSON/XHR/fetch responses whose URL or body references hotlist concepts such as:
   - `arithmetic`
   - `index`
   - `hot`
   - `sentence`
   - `rank`
   - `creator-count`
4. Classify responses into realtime or rising lists by tab/list labels, response fields, request parameters, or nearby DOM context.
5. Normalize each row into the table contract.
6. If network classification is incomplete, parse the visible tables/cards from DOM and save the DOM HTML/text evidence in `raw_payload`.

## Detail Capture Strategy

For each hotlist row:

1. Open the detail URL or click the row in the logged-in page.
2. Wait for "热门内容".
3. Select the leftmost visible video card in that section.
4. Extract visible fields and network payloads for the selected video.
5. Open the video detail URL or fetch the detail endpoint if available.
6. Capture top comments until 50 unique comments or exhaustion.

The selection rule is visual-leftmost. Do not swap to a different video because it has more comments.

Known implementation traps and fixes:

- Creator detail pages often render "热门内容" only after scroll. Always scroll the label into view, then wait for cards.
- The left navigation can satisfy broad video/card selectors. Filter candidates by the hot-content label position and by a minimum left coordinate past the sidebar.
- Pick the smallest visible label/tab element when switching between realtime and rising lists; large wrapper nodes can click the wrong area.
- Treat "内容为空/共0条记录" as a transient page state when either hotlist is empty; retry the index page once.
- The index page can reopen on a remembered list/page state. Before reading each hotlist, activate its label and page 1, then collect pages 2 and 3.
- Real comments are not available on the topic detail page. Open the selected video page and accept comments only from comment/reply network payloads or comment DOM on `www.douyin.com/share/video/...` / `/video/...`.
- If a video page asks for login, CAPTCHA, SMS, or risk verification, stop and request human help. Do not attempt to bypass verification.

## AI Media Analysis

Use reliable platform fields first:

- ASR/transcript/subtitle text for audio.
- OCR/frame summary/cover description/video summary for visual content.

When those are missing and media URLs or playable pages are available:

1. Download a short evidence bundle under `output/douyin-creator-index-media/<batch>/`.
2. For visual analysis, set `DOUYIN_CREATOR_CAPTURE_FRAMES=1`; save frame screenshots under `output/douyin-creator-index-frames/<batch>/` and pass them to `codex exec --image`.
3. Try `DOUYIN_AI_ANALYZER=claude` via `CLAUDE_CLI_EXE` for text/platform evidence.
4. Try `DOUYIN_AI_ANALYZER=codex` via `CODEX_CLI_EXE` when frame screenshots are available.
5. Store summaries plus evidence source and limitations in `content_evidence`.

Never claim direct audio or frame understanding when the analyzer did not inspect the media.

## Validation Queries

Latest batch counts:

```sql
select capture_batch_id, count(*) from douyin_realtime_hotspots group by capture_batch_id order by max(captured_at) desc limit 3;
select capture_batch_id, count(*) from douyin_rising_hotspots group by capture_batch_id order by max(captured_at) desc limit 3;
```

Rank coverage:

```sql
select rank, count(*) from douyin_realtime_hotspots where capture_batch_id = '<batch>' group by rank having count(*) > 1;
select rank, count(*) from douyin_rising_hotspots where capture_batch_id = '<batch>' group by rank having count(*) > 1;
```

Completion quality:

```sql
select capture_status, count(*) from douyin_realtime_hotspots where capture_batch_id = '<batch>' group by capture_status;
select capture_status, count(*) from douyin_rising_hotspots where capture_batch_id = '<batch>' group by capture_status;
```
