from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import Page, sync_playwright


PROJECT_DIR = Path(__file__).resolve().parent
LOG_ROOT = PROJECT_DIR / "logs" / "ui-smoke"
APP_URL = "http://127.0.0.1:8000"


@dataclass(slots=True)
class ScenarioResult:
    name: str
    status: str
    source_mode: str
    user_output_dir: str
    report_file: str
    downloaded: int
    skipped: int
    failed: int
    screenshot_before: str
    screenshot_after: str
    api_response_file: str


def wait_for_server(url: str, timeout_sec: int = 60) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=5):
                return
        except URLError:
            time.sleep(0.5)
    raise TimeoutError(f"Server did not start in {timeout_sec}s: {url}")


def start_ui_server(run_dir: Path) -> tuple[subprocess.Popen, Path]:
    server_log = run_dir / "ui_server.log"
    log_f = server_log.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=PROJECT_DIR,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
    )
    try:
        wait_for_server(APP_URL, timeout_sec=60)
    except Exception:
        proc.terminate()
        proc.wait(timeout=10)
        raise
    return proc, server_log


def fill_form(
    page: Page,
    username_or_url: str,
    output_dir: str,
    media_type: str,
    fallback_author_id: bool,
) -> None:
    page.fill("input[name='username_or_url']", username_or_url)
    page.select_option("select[name='media_type']", media_type)
    page.fill("input[name='output_dir']", output_dir)
    page.fill("input[name='max_pages']", "1")
    page.fill("input[name='max_items']", "5")
    page.fill("input[name='max_downloads']", "1")
    page.locator("input[name='metadata_only']").set_checked(False)
    page.locator("input[name='fallback_author_id']").set_checked(fallback_author_id)
    page.locator("input[name='no_progress']").set_checked(True)


def run_scenario(
    page: Page,
    run_dir: Path,
    name: str,
    username_or_url: str,
    media_type: str,
    fallback_author_id: bool,
) -> ScenarioResult:
    page.goto(APP_URL, wait_until="domcontentloaded")
    fill_form(
        page=page,
        username_or_url=username_or_url,
        output_dir=f"G:/tmp/task10_ui_smoke_{name}",
        media_type=media_type,
        fallback_author_id=fallback_author_id,
    )

    before_path = run_dir / f"{name}_before.png"
    after_path = run_dir / f"{name}_after.png"
    api_path = run_dir / f"{name}_api.json"
    page.screenshot(path=str(before_path), full_page=True)

    with page.expect_response(lambda r: r.url.endswith("/run") and r.request.method == "POST", timeout=240000) as resp_info:
        page.click("#startBtn")
    response = resp_info.value
    payload = response.json()
    api_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    page.wait_for_function(
        "document.getElementById('statusText').textContent.trim() === 'success'",
        timeout=240000,
    )
    page.screenshot(path=str(after_path), full_page=True)

    if payload.get("status") != "success":
        raise AssertionError(f"{name}: API returned non-success status: {payload}")

    required = ["user_output_dir", "report_file", "downloaded", "skipped", "failed", "source_mode"]
    for key in required:
        if key not in payload:
            raise AssertionError(f"{name}: missing key in API response: {key}")

    return ScenarioResult(
        name=name,
        status=str(payload["status"]),
        source_mode=str(payload["source_mode"]),
        user_output_dir=str(payload["user_output_dir"]),
        report_file=str(payload["report_file"]),
        downloaded=int(payload["downloaded"]),
        skipped=int(payload["skipped"]),
        failed=int(payload["failed"]),
        screenshot_before=str(before_path),
        screenshot_after=str(after_path),
        api_response_file=str(api_path),
    )


def main() -> int:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    run_dir = LOG_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    server_proc = None
    results: list[ScenarioResult] = []
    try:
        server_proc, server_log = start_ui_server(run_dir)

        scenarios = [
            ("nexblend_images", "https://civitai.com/user/NexBlend/images", "all", True),
            ("nexblend_videos", "https://civitai.com/user/NexBlend/videos", "all", True),
            ("lannfield_fallback_on", "https://civitai.com/user/Lannfield/images", "image", True),
            ("lannfield_fallback_off", "https://civitai.com/user/Lannfield/images", "image", False),
        ]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1080})
            page = context.new_page()
            for name, url, media_type, fallback in scenarios:
                print(f"[ui-smoke] running scenario={name}")
                result = run_scenario(page, run_dir, name, url, media_type, fallback)
                results.append(result)
                print(f"[ui-smoke] done scenario={name} status={result.status} source_mode={result.source_mode}")
            context.close()
            browser.close()

        summary = {
            "status": "PASS",
            "run_dir": str(run_dir),
            "server_log": str(server_log),
            "results": [asdict(r) for r in results],
        }
        (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    finally:
        if server_proc is not None and server_proc.poll() is None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
