#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import civitai_gallery_downloader as downloader


app = FastAPI(title="Civitai Downloader UI", version="0.1.0")


class RunRequest(BaseModel):
    username_or_url: str = Field(min_length=1)
    media_type: Literal["image", "video", "all"] = "image"
    output_dir: str = "output"
    max_pages: int | None = None
    max_items: int | None = None
    max_downloads: int | None = None
    metadata_only: bool = False
    fallback_author_id: bool = True
    no_progress: bool = False


def build_cli_args(payload: RunRequest) -> list[str]:
    args: list[str] = [payload.username_or_url, "--media-type", payload.media_type, "--output-dir", payload.output_dir]
    if payload.max_pages is not None:
        args.extend(["--max-pages", str(payload.max_pages)])
    if payload.max_items is not None:
        args.extend(["--max-items", str(payload.max_items)])
    if payload.max_downloads is not None:
        args.extend(["--max-downloads", str(payload.max_downloads)])
    if payload.metadata_only:
        args.append("--metadata-only")
    if payload.no_progress:
        args.append("--no-progress")
    if payload.fallback_author_id:
        args.append("--fallback-author-id")
    else:
        args.append("--no-fallback-author-id")
    return args


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Civitai Downloader UI MVP</title>
  <style>
    body { font-family: "Segoe UI", Tahoma, sans-serif; background:#f5f7fb; color:#1a2433; margin:0; }
    .wrap { max-width: 860px; margin: 28px auto; background:#fff; border-radius:14px; padding:20px; box-shadow:0 8px 28px rgba(22,34,66,.08); }
    h1 { margin:0 0 16px; font-size:24px; }
    .grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
    label { display:flex; flex-direction:column; font-size:13px; gap:6px; }
    input, select { padding:10px; border:1px solid #c9d3e5; border-radius:9px; font-size:14px; }
    .checks { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:8px; }
    .checks label { flex-direction:row; align-items:center; gap:8px; font-size:14px; }
    button { margin-top:14px; width:100%; background:#1258dc; color:#fff; border:none; padding:12px; border-radius:10px; font-size:15px; cursor:pointer; }
    button:disabled { background:#8ba9e6; cursor:default; }
    .panel { margin-top:14px; padding:12px; border-radius:10px; background:#f1f5ff; white-space:pre-wrap; word-break:break-word; }
    .status-running { color:#8a5a00; }
    .status-success { color:#056b37; }
    .status-error { color:#a10025; }
    @media (max-width: 760px) { .grid { grid-template-columns:1fr; } .checks { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Civitai Downloader UI MVP</h1>
    <form id="runForm">
      <div class="grid">
        <label>username_or_url
          <input name="username_or_url" value="https://civitai.com/user/NexBlend/images" required />
        </label>
        <label>media_type
          <select name="media_type">
            <option value="image">image</option>
            <option value="video">video</option>
            <option value="all">all</option>
          </select>
        </label>
        <label>output_dir
          <input name="output_dir" value="output_ui" />
        </label>
        <label>max_pages
          <input name="max_pages" type="number" min="1" placeholder="empty = no limit" />
        </label>
        <label>max_items
          <input name="max_items" type="number" min="1" placeholder="empty = no limit" />
        </label>
        <label>max_downloads
          <input name="max_downloads" type="number" min="1" placeholder="empty = no limit" />
        </label>
      </div>
      <div class="checks">
        <label><input type="checkbox" name="metadata_only" /> metadata_only</label>
        <label><input type="checkbox" name="fallback_author_id" checked /> fallback_author_id</label>
        <label><input type="checkbox" name="no_progress" checked /> no_progress</label>
      </div>
      <button id="startBtn" type="submit">Start</button>
    </form>

    <div class="panel"><strong>Status:</strong> <span id="statusText">idle</span></div>
    <div class="panel"><strong>Results:</strong>
<div id="resultsText">output_path: -
report_path: -</div></div>
  </div>

  <script>
    const form = document.getElementById("runForm");
    const btn = document.getElementById("startBtn");
    const statusText = document.getElementById("statusText");
    const resultsText = document.getElementById("resultsText");

    function setStatus(text, cls) {
      statusText.textContent = text;
      statusText.className = cls;
    }

    function numberOrNull(value) {
      if (value === "" || value == null) return null;
      return Number(value);
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      btn.disabled = true;
      setStatus("running", "status-running");
      resultsText.textContent = "output_path: -\\nreport_path: -";

      const formData = new FormData(form);
      const payload = {
        username_or_url: String(formData.get("username_or_url") || "").trim(),
        media_type: String(formData.get("media_type") || "image"),
        output_dir: String(formData.get("output_dir") || "output"),
        max_pages: numberOrNull(String(formData.get("max_pages") || "")),
        max_items: numberOrNull(String(formData.get("max_items") || "")),
        max_downloads: numberOrNull(String(formData.get("max_downloads") || "")),
        metadata_only: formData.get("metadata_only") !== null,
        fallback_author_id: formData.get("fallback_author_id") !== null,
        no_progress: formData.get("no_progress") !== null
      };

      try {
        const response = await fetch("/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok || data.status === "error") {
          throw new Error(data.message || data.detail || "Execution failed");
        }
        setStatus("success", "status-success");
        resultsText.textContent =
          "output_path: " + data.user_output_dir + "\\n" +
          "report_path: " + data.report_file + "\\n" +
          "source_mode: " + data.source_mode + "\\n" +
          "downloaded/skipped/failed: " + data.downloaded + "/" + data.skipped + "/" + data.failed;
      } catch (error) {
        setStatus("error", "status-error");
        resultsText.textContent = "error: " + (error.message || String(error));
      } finally {
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


@app.post("/run")
def run_job(payload: RunRequest) -> dict[str, object]:
    try:
        argv = build_cli_args(payload)
        config = downloader.parse_args(argv)
        result = downloader.run_download(config)
        return {
            "status": "success",
            "message": "completed",
            "username": result.username,
            "source_mode": result.source_mode,
            "metadata_file": str(result.metadata_file),
            "report_file": str(result.report_file),
            "user_output_dir": str(result.user_output_dir),
            "downloaded": result.downloaded,
            "skipped": result.skipped,
            "failed": result.failed,
        }
    except (argparse.ArgumentError, SystemExit) as exc:
        return {"status": "error", "message": f"Invalid input: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
