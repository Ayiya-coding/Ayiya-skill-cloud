---
name: xiaodouya-ip-backend
description: Operate Xinbang Xiaodouya Windows client to collect owned IP account backend data for the media-coding project. Use when Codex needs to open 小豆芽, find the account-manager list matching the active IP name, check highlighted versus gray login state, open Douyin/视频号/Xiaohongshu/Weibo/Bilibili creator backends, capture post metrics/material evidence, or persist those rows into the local database.
---

# Xiaodouya IP Backend

## Core Rule

Treat Xiaodouya as the account-backend entrypoint, not as the final data source. The source of truth is the platform backend page opened inside Xiaodouya for the selected owned account.

Workflow:

1. Launch `D:\Program Files (x86)\xiaodouya\新榜小豆芽.exe`.
2. Read the active IP name from the product IP selector, for example `我是Ayiya`.
3. In Xiaodouya Account Manager, open the list whose name exactly matches that IP name.
4. For each platform account in the list:
   - if the account row is gray/disabled, mark it as needing manual login or verification and do not scrape that account;
   - if the row is highlighted/active, open the corresponding platform backend.
5. In the opened backend's Works/Content Management page, collect the newest visible works:
   - platform post id or stable backend URL
   - title
   - publish date and time
   - caption/post text and extracted text content when visible
   - play/view count
   - like count
   - comment count
   - share count
   - collect/favorite count
   - cover, image, and video material URLs or local cache paths when available
   - captured date and time
6. Persist account state, post rows, and metric snapshots into the media-coding PostgreSQL database.

## Guardrails

- Never bypass login, captcha, SMS, slider, or risk verification. Stop and ask the user to complete it in Xiaodouya.
- Never fabricate complete batches. If a platform page is incomplete or blocked, save the blocker in `raw_payload.capture_status` and continue with other active accounts.
- Do not merge accounts across IP names. The Xiaodouya list name must match the current IP selector value.
- Do not print or store cookies, tokens, or session headers. It is safe to store cookie names, login-present flags, and blocker types.
- If the embedded backend exposes a normal browser/CDP target, prefer DOM/network extraction. If not, use Windows UI automation only to navigate and export visible data.

## media-coding Contract

Project root: `D:\media-coding`

Expected script:

- `src/server/scripts/scrape-xiaodouya-ip-backends.ts`

Expected command:

- `npm run scrape:xiaodouya-ip-backends`

Expected environment:

- `XIAODOUYA_EXE=D:\Program Files (x86)\xiaodouya\新榜小豆芽.exe`
- `IP_PROFILE_NAME=我是Ayiya`
- `XIAODOUYA_PLATFORM=douyin|wechat|xiaohongshu|weibo|bilibili` for targeted runs
- `XIAODOUYA_MAX_POSTS=30`

Database expectations:

- `ip_profiles` stores the owned IP name.
- `ip_accounts` stores one platform account under an IP profile.
- `ip_posts` stores the current normalized post row.
- `ip_post_metric_snapshots` stores every capture-time metric snapshot for trends.
- `ai_analysis` with target `ip_post` stores per-post operation analysis.

## Validation Checklist

After a run:

- The selected Xiaodouya list name equals the active IP name.
- Gray accounts are recorded as manual-intervention blockers, not retried in a tight loop.
- Each saved post has a captured timestamp and at least one stable id or URL.
- The latest `ip_posts` values match the newest snapshot for that post.
- Material buttons only become active when local or remote material evidence exists.
- No credentials or cookie values are present in logs, DB rows, or output files.
