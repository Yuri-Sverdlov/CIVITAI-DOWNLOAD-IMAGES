# NEXT_SESSION

## Проект

- Путь: `G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES`
- Работать только в этом проекте.
- Подпроект `COMFYUI-API-CHAT` не изменять.

## Основные правила работы

1. Перед началом читать:
   - `Agent Context.md`
   - `Agent Report.md`
   - `BASELINE.md`
2. Не ломать baseline-поведение CLI:
   - username/URL автора (`/images` и `/videos`)
   - default media type = `image`
   - `--media-type image|video|all`
   - fallback ON/OFF
   - лимиты `--max-items`, `--max-downloads`
   - отчёты в snake_case
3. Любые долгие проверки запускать через `bg-runner`:
   - `G:\AI\_MY_PROGRAMMING_3\_AGENT-TOOLS\bg-runner`
4. Обязательно писать регулярные апдейты статуса в процессе проверок.
5. После завершения обновлять `Agent Report.md`:
   - команды
   - job_id
   - PASS/FAIL
   - что исправлено
   - где логи/скриншоты

## Что уже реализовано

1. CLI downloader с поддержкой image/video/all.
2. Детальные `metadata_*.json` и `report_*.json`.
3. Fallback:
   - сначала query по `username`
   - при 0 items fallback по `author_id` со страницы автора
   - режим в отчёте: `source_mode`
4. UI MVP на FastAPI:
   - файл: `app.py`
   - запуск: `python .\app.py` или `uvicorn app:app --reload`
5. Авто-smoke UI через Playwright:
   - файл: `ui_smoke_playwright.py`
   - артефакты: `.\logs\ui-smoke\<timestamp>\`

## Проблемы, которые уже встречались

1. Долгие foreground-команды прерывались пользователем, потому что не было видимого прогресса.
2. В sandbox были `Access denied` на некоторые операции записи.
3. `unittest` падал с `No space left on device` из-за temp-пути окружения.
4. В первой версии UI smoke-сценария Lannfield ON/OFF проверялся недостаточно явно.

## Как решали

1. Перевели долгие проверки в background через `bg-runner` + polling через `status.py`.
2. Для операций с правами использовали запуск с эскалацией.
3. Для тестов задавали `TEMP/TMP` в проектный writable путь (`output_livecheck`).
4. Доработали `ui_smoke_playwright.py`:
   - per-scenario `media_type`
   - явный `media_type=image` для Lannfield fallback ON/OFF.

## Что делать, чтобы не повторять проблемы

1. По умолчанию запускать длинные проверки только через `bg-runner`.
2. Сразу после `launch.py` фиксировать `job_id` и путь к логам в отчёте.
3. Делать polling `status.py` каждые 20-30 секунд.
4. Перед `unittest` при необходимости выставлять:
   - `TEMP=...\output_livecheck`
   - `TMP=...\output_livecheck`
5. Для UI smoke всегда сохранять:
   - before/after screenshots
   - `*_api.json`
   - `summary.json`
6. Если сценарии проходят, но проверка недостаточно строгая — сначала усилить сценарий, затем перезапустить.

## Полезные команды

```powershell
# Запуск background job
python "G:\AI\_MY_PROGRAMMING_3\_AGENT-TOOLS\bg-runner\launch.py" --cmd "python .\ui_smoke_playwright.py" --name "task-ui-smoke" --logs-dir ".\logs"

# Статус job
python "G:\AI\_MY_PROGRAMMING_3\_AGENT-TOOLS\bg-runner\status.py" --job-id <JOB_ID> --logs-dir ".\logs" --tail 50

# Базовые тесты
python -m unittest -v .\test_downloader_core.py
```

## Где смотреть последние артефакты

- `.\logs\`
- `.\logs\ui-smoke\`
- `Agent Report.md`
