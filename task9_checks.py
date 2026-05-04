from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent


def run_cmd(cmd: list[str]) -> None:
    print(f"[task9] RUN: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True)
    print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, flush=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")


def ui_smoke(username_or_url: str, output_dir: str) -> None:
    from fastapi.testclient import TestClient  # type: ignore
    import app

    payload = {
        "username_or_url": username_or_url,
        "media_type": "all",
        "output_dir": output_dir,
        "max_pages": 1,
        "max_items": 5,
        "max_downloads": 1,
        "metadata_only": False,
        "fallback_author_id": True,
        "no_progress": True,
    }
    client = TestClient(app.app)
    response = client.post("/run", json=payload)
    print(f"[task9] UI {username_or_url} status_code={response.status_code}", flush=True)
    data = response.json()
    print(f"[task9] UI payload result: {json.dumps(data, ensure_ascii=False)}", flush=True)
    if response.status_code != 200 or data.get("status") != "success":
        raise RuntimeError(f"UI smoke failed for {username_or_url}")


def main() -> int:
    os.environ["TEMP"] = str(PROJECT_DIR / "output_livecheck")
    os.environ["TMP"] = str(PROJECT_DIR / "output_livecheck")

    run_cmd([sys.executable, "-m", "unittest", "-v", ".\\test_downloader_core.py"])
    ui_smoke("https://civitai.com/user/NexBlend/images", "G:/tmp/task9_ui_smoke_images")
    ui_smoke("https://civitai.com/user/NexBlend/videos", "G:/tmp/task9_ui_smoke_videos")
    print("[task9] ALL CHECKS PASSED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
