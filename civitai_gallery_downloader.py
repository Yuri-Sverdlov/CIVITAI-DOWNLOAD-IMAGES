#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode, urlparse
from urllib.request import Request, urlopen

from tqdm import tqdm


API_URL = "https://civitai.com/api/v1/images"
USER_AGENT = "civitai-gallery-downloader/2.0"


# Mapping of media types to extensions
MEDIA_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "video": [".mp4", ".webm", ".mov"],
}


def parse_nsfw_filter(value: str) -> str | None:
    normalized = value.strip().lower()
    aliases = {
        "none": None,
        "off": None,
        "disable": None,
        "disabled": None,
        "omit": None,
        "soft": "Soft",
        "mature": "Mature",
        "x": "X",
        "true": "true",
        "false": "false",
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise argparse.ArgumentTypeError(
            "--nsfw must be one of: none, off, soft, mature, x, true, false"
        ) from exc


def parse_media_type(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in ("image", "video", "all"):
        return normalized
    raise argparse.ArgumentTypeError(
        "--media-type must be one of: image, video, all"
    )


def parse_username_or_author_url(value: str) -> str:
    raw_value = value.strip()
    if not raw_value:
        raise argparse.ArgumentTypeError("username cannot be empty")

    parsed = urlparse(raw_value)
    if parsed.scheme and parsed.netloc:
        host = parsed.netloc.lower()
        if host not in ("civitai.com", "www.civitai.com"):
            raise argparse.ArgumentTypeError(
                "Author URL host must be civitai.com"
            )

        path_parts = [segment for segment in parsed.path.split("/") if segment]
        if len(path_parts) >= 3 and path_parts[0] == "user" and path_parts[2] in ("images", "videos"):
            username = unquote(path_parts[1]).strip()
            if username:
                return username

        raise argparse.ArgumentTypeError(
            "Author URL must be: https://civitai.com/user/<username>/images or /videos"
        )

    return raw_value


@dataclass(slots=True)
class Config:
    username: str
    output_dir: Path
    limit: int
    nsfw: str | None
    sort: str
    period: str | None
    page_delay: float
    download_delay: float
    max_pages: int | None
    max_items: int | None
    max_downloads: int | None
    download_media: bool
    overwrite_metadata: bool
    media_type: str  # "image", "video", "all"
    no_progress: bool
    fallback_author_id: bool


@dataclass
class DownloadReport:
    """Report entry for a single download attempt."""
    item_id: int | None
    status: str  # "downloaded", "skipped", "failed"
    reason: str | None
    url: str | None
    file_path: str | None
    content_type: str | None
    size_bytes: int | None
    duration_ms: int | None


@dataclass(slots=True)
class RunResult:
    username: str
    source_mode: str
    metadata_file: Path
    report_file: Path
    user_output_dir: Path
    downloaded: int
    skipped: int
    failed: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Downloads a Civitai creator gallery via the public images API, "
            "saving metadata and optionally the media files."
        )
    )
    parser.add_argument(
        "username",
        type=parse_username_or_author_url,
        help="Civitai username or author URL (/user/<username>/images or /videos)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for metadata and downloaded files (default: output)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="API page size, typically up to 100 (default: 100)",
    )
    parser.add_argument(
        "--nsfw",
        type=parse_nsfw_filter,
        default=None,
        metavar="{none|off|soft|mature|x|true|false}",
        help=(
            "Optional NSFW filter. Use none/off to omit the filter, "
            "or pass soft, mature, x, true, false to forward that value to the API."
        ),
    )
    parser.add_argument(
        "--sort",
        choices=("Newest", "Oldest", "Most Reactions", "Most Comments"),
        default="Newest",
        help="Sort order for gallery items (default: Newest)",
    )
    parser.add_argument(
        "--period",
        choices=("AllTime", "Year", "Month", "Week", "Day"),
        default=None,
        help="Optional period filter",
    )
    parser.add_argument(
        "--page-delay",
        type=float,
        default=1.0,
        help="Delay in seconds between API page requests (default: 1.0)",
    )
    parser.add_argument(
        "--download-delay",
        type=float,
        default=0.25,
        help="Delay in seconds between file downloads (default: 0.25)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page limit",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Optional cap on collected metadata items",
    )
    parser.add_argument(
        "--max-downloads",
        type=int,
        default=None,
        help="Optional cap on downloaded media files",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Skip media download and save metadata only",
    )
    parser.add_argument(
        "--overwrite-metadata",
        action="store_true",
        help="Overwrite metadata file instead of timestamping it",
    )
    parser.add_argument(
        "--media-type",
        type=parse_media_type,
        default="image",
        choices=("image", "video", "all"),
        help="Filter media type: image, video, or all (default: image)",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar display",
    )
    fallback_group = parser.add_mutually_exclusive_group()
    fallback_group.add_argument(
        "--fallback-author-id",
        dest="fallback_author_id",
        action="store_true",
        help="Enable fallback via author page userId lookup (default: enabled)",
    )
    fallback_group.add_argument(
        "--no-fallback-author-id",
        dest="fallback_author_id",
        action="store_false",
        help="Disable fallback via author page userId lookup",
    )
    parser.set_defaults(fallback_author_id=True)
    return parser


def parse_args(argv: list[str]) -> Config:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.max_pages is not None and args.max_pages < 1:
        parser.error("--max-pages must be at least 1")
    if args.max_items is not None and args.max_items < 1:
        parser.error("--max-items must be at least 1")
    if args.max_downloads is not None and args.max_downloads < 1:
        parser.error("--max-downloads must be at least 1")
    if args.page_delay < 0 or args.download_delay < 0:
        parser.error("Delays cannot be negative")

    return Config(
        username=args.username,
        output_dir=Path(args.output_dir),
        limit=args.limit,
        nsfw=args.nsfw,
        sort=args.sort,
        period=args.period,
        page_delay=args.page_delay,
        download_delay=args.download_delay,
        max_pages=args.max_pages,
        max_items=args.max_items,
        max_downloads=args.max_downloads,
        download_media=not args.metadata_only,
        overwrite_metadata=args.overwrite_metadata,
        media_type=args.media_type,
        no_progress=args.no_progress,
        fallback_author_id=args.fallback_author_id,
    )


def http_get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    request_url = url
    if params:
        request_url = f"{url}?{urlencode(params)}"

    request = Request(
        request_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def http_get_text(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def http_download(url: str, destination: Path) -> int:
    """Download file and return size in bytes."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    total_size = 0
    with urlopen(request, timeout=60) as response, destination.open("wb") as file_obj:
        while True:
            chunk = response.read(1024 * 128)
            if not chunk:
                break
            file_obj.write(chunk)
            total_size += len(chunk)
    return total_size


def should_include_item(item: dict[str, Any], media_type: str) -> bool:
    """Check if item should be included based on media type filter."""
    if media_type == "all":
        return True
    item_type = item.get("type", "image")
    return item_type == media_type


def build_common_params(config: Config) -> dict[str, Any]:
    params: dict[str, Any] = {
        "limit": config.limit,
        "sort": config.sort,
    }
    if config.nsfw is not None:
        params["nsfw"] = config.nsfw
    if config.period:
        params["period"] = config.period
    return params


def extract_author_id_from_page(username: str) -> int | None:
    page_urls = [
        f"https://civitai.com/user/{username}/images",
        f"https://civitai.com/user/{username}/videos",
    ]
    for page_url in page_urls:
        try:
            html = http_get_text(page_url)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            print(f"Could not fetch author page {page_url}: {exc}")
            continue

        match = re.search(r'"userId"\s*:\s*(\d+)', html)
        if match:
            return int(match.group(1))
    return None


def collect_items_with_params(
    config: Config,
    params: dict[str, Any],
    source_mode: str,
) -> list[dict[str, Any]]:
    all_items: list[dict[str, Any]] = []
    page_number = 1
    next_url: str | None = API_URL
    next_params: dict[str, Any] | None = dict(params)

    while next_url:
        if config.max_pages is not None and page_number > config.max_pages:
            print(f"Reached --max-pages={config.max_pages}, stopping page fetch.")
            break

        print(f"Fetching page {page_number} [{source_mode}]...")
        payload = http_get_json(next_url, next_params)
        items = payload.get("items", [])
        if not items:
            print("No items returned, stopping.")
            break

        # Filter by media type
        filtered_items = [item for item in items if should_include_item(item, config.media_type)]
        all_items.extend(filtered_items)
        print(f"Collected {len(filtered_items)} items on page {page_number} (total {len(all_items)}).")

        if config.max_items is not None and len(all_items) >= config.max_items:
            print(f"Reached --max-items={config.max_items}, trimming and stopping.")
            all_items = all_items[: config.max_items]
            break

        metadata = payload.get("metadata") or {}
        next_page = metadata.get("nextPage")
        if not next_page:
            break

        next_url = str(next_page)
        next_params = None
        page_number += 1

        if config.page_delay:
            time.sleep(config.page_delay)

    return all_items


def collect_images(config: Config) -> tuple[list[dict[str, Any]], str]:
    common_params = build_common_params(config)
    username_params = dict(common_params)
    username_params["username"] = config.username

    items = collect_items_with_params(config, username_params, "username_query")
    source_mode = "username_query"

    if not items and config.fallback_author_id:
        print("Username query returned 0 items; trying author_id fallback.")
        author_id = extract_author_id_from_page(config.username)
        if author_id is None:
            print("Could not resolve author_id from author page; keeping empty result.")
            return items, source_mode

        print(f"Resolved author_id={author_id}. Trying author_id query.")
        for key in ("userId", "user_id"):
            fallback_params = dict(common_params)
            fallback_params[key] = author_id
            fallback_items = collect_items_with_params(config, fallback_params, "author_id_query")
            if fallback_items:
                source_mode = "author_id_query"
                print(f"Fallback succeeded via '{key}' parameter.")
                return fallback_items, source_mode
        print("Fallback author_id query returned 0 items; keeping empty result.")

    return items, source_mode


def flatten_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "postId": item.get("postId"),
        "url": item.get("url"),
        "username": item.get("username"),
        "name": item.get("name"),
        "type": item.get("type", "image"),
        "nsfwLevel": item.get("nsfwLevel"),
        "nsfw": item.get("nsfw"),
        "createdAt": item.get("createdAt"),
        "width": item.get("width"),
        "height": item.get("height"),
        "mimeType": item.get("mimeType"),
        "hash": item.get("hash"),
        "meta": item.get("meta"),
        "stats": item.get("stats"),
        "generationProcess": item.get("generationProcess"),
    }


def get_user_dir(config: Config) -> Path:
    """Get base directory for user: output_dir/username/"""
    user_dir = config.output_dir / config.username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def metadata_path(config: Config) -> Path:
    user_dir = get_user_dir(config)
    if config.overwrite_metadata:
        return user_dir / "metadata.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return user_dir / f"metadata_{timestamp}.json"


def report_path(config: Config) -> Path:
    """Generate report file path with timestamp."""
    user_dir = get_user_dir(config)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return user_dir / f"report_{timestamp}.json"


def save_metadata(config: Config, items: list[dict[str, Any]], source_mode: str) -> Path:
    output = {
        "username": config.username,
        "fetchedAt": datetime.now().isoformat(timespec="seconds"),
        "source_mode": source_mode,
        "count": len(items),
        "filters": {
            "limit": config.limit,
            "nsfw": config.nsfw,
            "sort": config.sort,
            "period": config.period,
            "maxPages": config.max_pages,
            "maxItems": config.max_items,
            "mediaType": config.media_type,
        },
        "items": [flatten_item(item) for item in items],
    }

    destination = metadata_path(config)
    destination.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def save_report(config: Config, reports: list[DownloadReport], source_mode: str) -> Path:
    """Save detailed download report to JSON."""
    output = {
        "username": config.username,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "media_type": config.media_type,
        "source_mode": source_mode,
        "counters": {
            "downloaded": sum(1 for r in reports if r.status == "downloaded"),
            "skipped": sum(1 for r in reports if r.status == "skipped"),
            "failed": sum(1 for r in reports if r.status == "failed"),
        },
        "items": [
            {
                "id": r.item_id,
                "status": r.status,
                "reason": r.reason,
                "url": r.url,
                "file_path": r.file_path,
                "content_type": r.content_type,
                "size_bytes": r.size_bytes,
                "duration_ms": r.duration_ms,
            }
            for r in reports
        ],
    }

    destination = report_path(config)
    destination.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def safe_suffix_from_url(url: str, mime_type: str | None, item_type: str = "image") -> str:
    """Extract file extension from URL or guess from mime type."""
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    
    # Validate suffix against known extensions
    all_extensions = MEDIA_EXTENSIONS["image"] + MEDIA_EXTENSIONS["video"]
    if suffix in all_extensions:
        return suffix
    
    # Try to guess from mime type
    if mime_type:
        guessed = mimetypes.guess_extension(mime_type)
        if guessed:
            return guessed
    
    # Default based on item type
    if item_type == "video":
        return ".mp4"
    return ".jpg"


def get_media_dir(config: Config, item_type: str) -> Path:
    """Get appropriate media directory based on item type."""
    user_dir = get_user_dir(config)
    if item_type == "video":
        return user_dir / "video"
    return user_dir / "images"


def download_items(
    config: Config,
    items: list[dict[str, Any]],
    source_mode: str,
) -> tuple[int, int, int, Path | None]:
    """Download media items and generate report. Returns (downloaded, skipped, failed, report_path)."""
    reports: list[DownloadReport] = []
    downloaded = 0
    skipped = 0
    failed = 0

    use_progress = not config.no_progress and sys.stdout.isatty()
    progress = tqdm(total=len(items), desc="Downloading", unit="file") if use_progress else None

    for idx, item in enumerate(items):
        if config.max_downloads is not None and downloaded >= config.max_downloads:
            for remaining_item in items[idx:]:
                reports.append(DownloadReport(
                    item_id=remaining_item.get("id"),
                    status="skipped",
                    reason="max-downloads limit reached",
                    url=remaining_item.get("url"),
                    file_path=None,
                    content_type=remaining_item.get("type", "image"),
                    size_bytes=None,
                    duration_ms=None,
                ))
                skipped += 1
            if use_progress:
                tqdm.write(f"Reached --max-downloads={config.max_downloads}, stopping downloads.")
                progress.update(len(items) - idx)
            else:
                print(f"Reached --max-downloads={config.max_downloads}, stopping downloads.")
            break

        url = item.get("url")
        item_id = item.get("id")
        item_type = item.get("type", "image")
        
        if not url or not item_id:
            reports.append(DownloadReport(
                item_id=item_id,
                status="skipped",
                reason="missing URL or ID",
                url=url,
                file_path=None,
                content_type=item_type,
                size_bytes=None,
                duration_ms=None,
            ))
            skipped += 1
            if progress:
                progress.update(1)
            continue

        suffix = safe_suffix_from_url(url, item.get("mimeType"), item_type)
        media_dir = get_media_dir(config, item_type)
        destination = media_dir / f"{item_id}{suffix}"
        
        if destination.exists():
            file_size = destination.stat().st_size
            reports.append(DownloadReport(
                item_id=item_id,
                status="skipped",
                reason="file already exists",
                url=url,
                file_path=str(destination),
                content_type=item_type,
                size_bytes=file_size,
                duration_ms=None,
            ))
            skipped += 1
            if progress:
                progress.update(1)
            continue

        start_time = time.time()
        try:
            media_dir.mkdir(parents=True, exist_ok=True)
            file_size = http_download(url, destination)
            duration_ms = int((time.time() - start_time) * 1000)
            
            reports.append(DownloadReport(
                item_id=item_id,
                status="downloaded",
                reason=None,
                url=url,
                file_path=str(destination),
                content_type=item_type,
                size_bytes=file_size,
                duration_ms=duration_ms,
            ))
            downloaded += 1
            if not use_progress:
                print(f"Downloaded {destination.name}")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            reports.append(DownloadReport(
                item_id=item_id,
                status="failed",
                reason=str(exc),
                url=url,
                file_path=None,
                content_type=item_type,
                size_bytes=None,
                duration_ms=duration_ms,
            ))
            failed += 1
            if use_progress:
                tqdm.write(f"Failed to download id={item_id}: {exc}")
            else:
                print(f"Failed to download id={item_id}: {exc}", file=sys.stderr)

        if config.download_delay:
            time.sleep(config.download_delay)

        if progress:
            progress.update(1)

    if progress:
        progress.close()

    report_file = save_report(config, reports, source_mode)
    return downloaded, skipped, failed, report_file


def run_download(config: Config) -> RunResult:
    items, source_mode = collect_images(config)
    print(f"Data source mode: {source_mode}")
    metadata_file = save_metadata(config, items, source_mode)
    print(f"Saved metadata: {metadata_file}")

    downloaded = 0
    skipped = 0
    failed = 0

    if config.download_media:
        downloaded, skipped, failed, report_file = download_items(config, items, source_mode)
        print(f"Downloads complete. Downloaded: {downloaded}, skipped: {skipped}, failed: {failed}")
        if report_file:
            print(f"Saved report: {report_file}")
    else:
        print("Metadata-only mode enabled; media download skipped.")
        metadata_only_report = [
            DownloadReport(
                item_id=item.get("id"),
                status="skipped",
                reason="metadata-only mode",
                url=item.get("url"),
                file_path=None,
                content_type=item.get("type", "image"),
                size_bytes=None,
                duration_ms=None,
            )
            for item in items
        ]
        report_file = save_report(config, metadata_only_report, source_mode)
        skipped = len(items)
        print(f"Saved report: {report_file}")

    return RunResult(
        username=config.username,
        source_mode=source_mode,
        metadata_file=metadata_file,
        report_file=report_file,
        user_output_dir=get_user_dir(config),
        downloaded=downloaded,
        skipped=skipped,
        failed=failed,
    )


def main(argv: list[str]) -> int:
    config = parse_args(argv)

    try:
        run_download(config)
        return 0
    except HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Network error: {exc.reason}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
