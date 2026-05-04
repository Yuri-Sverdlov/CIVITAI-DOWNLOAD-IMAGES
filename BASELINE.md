# Baseline Before Web UI

Date frozen: 2026-05-04
Project: CIVITAI-DOWNLOAD-IMAGES

## Scope
This baseline captures the CLI behavior that must stay stable before adding browser UI.

## Required behavior
1. Input supports username and author URLs:
   - /user/<username>/images
   - /user/<username>/videos
2. Default media behavior:
   - If --media-type is not provided, behavior is image-only.
3. Media filters:
   - --media-type image|video|all works.
4. Fallback behavior:
   - Username query first.
   - If zero results and fallback enabled, resolve author_id from author page and retry.
   - Report source_mode must show username_query or author_id_query.
5. Limits behavior:
   - --max-items and --max-downloads are enforced.
   - Skipped entries include reason: "max-downloads limit reached" when applicable.
6. Output layout:
   - <output>/<username>/images
   - <output>/<username>/video
   - Media folders are created only when that media type is actually downloaded.
7. Reports:
   - report_*.json exists for both normal mode and --metadata-only.
   - Snake_case keys are used: file_path, content_type, size_bytes, duration_ms, counters.

## Verification source
Validated by Task 7 runs and artifact checks under G:\tmp\task7_*.
