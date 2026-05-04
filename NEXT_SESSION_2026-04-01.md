# Next Session Notes

## Today

- Added a standalone script [civitai_gallery_downloader.py](g:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES\civitai_gallery_downloader.py) in the workspace root.
- Updated its behavior so NSFW filtering is applied only when `--nsfw` is explicitly passed.
- Added a short usage guide in [README.md](g:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES\README.md).
- Configured a PowerShell profile wrapper so `codex` can be launched from any project.
- Reviewed local project copy in `COMFYUI-API-CHAT`.

## Key Conclusion

Do not rebuild from scratch. Use `COMFYUI-API-CHAT` as the base and extend it.

Reasons:

- already has FastAPI backend;
- already has UI;
- already has ComfyUI integration;
- already has Civitai-related tools;
- missing piece is a stronger "gallery/author/filter assistant" flow.

## Recommended Next Steps

1. Add a dedicated backend module for Civitai gallery/author search with filters.
2. Add a tool for the agent that can fetch author images by username and filters.
3. Add a small UI panel for author URL/username, sorting, period, NSFW, tags, and download options.
4. Only use browser automation for filters that are not reliably available through the API.

## Important Notes

- In `COMFYUI-API-CHAT`, `git status` works only with a safe-directory override because of Windows ownership mismatch.
- The local repo remote currently points to:
  `https://github.com/Yuri-Sverdlov/COMFYUI-API-CHAT-HAIFA.git`
- User later provided another GitHub repo URL:
  `https://github.com/Yuri-Sverdlov/COMFYUI-SIVITAI-CHAT`
- Before any push, verify which remote should be the real target.

## Suggested Prompt For Tomorrow

```text
Read NEXT_SESSION_2026-04-01.md and continue the work.
Start by designing the backend module for Civitai author/gallery filtering inside COMFYUI-API-CHAT.
Then propose the minimum implementation plan for v1.
```
