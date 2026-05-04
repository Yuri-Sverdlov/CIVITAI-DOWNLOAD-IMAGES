# Civitai Gallery Downloader

Скрипт скачивает галерею автора через публичный API Civitai и сохраняет:

- метаданные (`metadata_*.json` или `metadata.json`);
- медиафайлы (изображения и/или видео);
- детальный отчёт (`report_<timestamp>.json`).

## Установка

```powershell
pip install tqdm
```

## Входные форматы автора

Поддерживаются оба варианта:

- `USERNAME`
- URL автора:
  - `https://civitai.com/user/<username>/images`
  - `https://civitai.com/user/<username>/videos`

Из URL автоматически извлекается `<username>`.

## Базовый запуск

```powershell
python .\civitai_gallery_downloader.py USERNAME
```

Пример с URL:

```powershell
python .\civitai_gallery_downloader.py "https://civitai.com/user/civitai/videos"
```

## Типы медиа

Флаг `--media-type image|video|all`:

- `image` (по умолчанию) - только изображения;
- `video` - только видео;
- `all` - изображения и видео.

Важно: даже если передан URL вида `/videos`, без `--media-type` всё равно используется дефолт `image` (обратная совместимость).

## Fallback по author_id

Если запрос к API по `username` вернул 0 элементов, скрипт может автоматически включить fallback:

1. читает страницу автора (`/images` или `/videos`);
2. извлекает `author_id` (`userId`) из HTML;
3. повторяет запрос к API через `userId`/`user_id`.

Это решает кейс: «страница автора существует и содержит контент, но API по username вернул пусто».

Управление:

- `--fallback-author-id` - включить fallback (по умолчанию включён);
- `--no-fallback-author-id` - отключить fallback.

## `--metadata-only`

Режим `--metadata-only`:

- сохраняет `metadata_*.json` (или `metadata.json` при `--overwrite-metadata`);
- обязательно создаёт `report_<timestamp>.json`;
- не скачивает медиа;
- не создаёт медиа-папки `images/` и `video/`.

```powershell
python .\civitai_gallery_downloader.py USERNAME --metadata-only
```

## Прогресс-бар

Прогресс-бар (`tqdm`) показывается автоматически только в TTY.  
Для отключения:

```powershell
python .\civitai_gallery_downloader.py USERNAME --no-progress
```

## Основные параметры

- `--output-dir` базовая папка результата;
- `--limit` размер страницы API;
- `--nsfw` NSFW-фильтр (`none|off|soft|mature|x|true|false`);
- `--sort` сортировка;
- `--period` период сортировки;
- `--max-pages` лимит страниц;
- `--max-items` лимит элементов;
- `--max-downloads` лимит скачиваний;
- `--metadata-only` только метаданные + отчёт;
- `--overwrite-metadata` перезаписать `metadata.json`;
- `--media-type` тип медиа: `image`, `video`, `all`;
- `--fallback-author-id` включить fallback по `author_id` (по умолчанию ON);
- `--no-fallback-author-id` отключить fallback по `author_id`;
- `--no-progress` отключить прогресс-бар.

## Поддерживаемые форматы

- Изображения: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`
- Видео: `.mp4`, `.webm`, `.mov`

## Структура папок

```
<output-dir>/
└── <USERNAME>/
    ├── images/              # создаётся только если скачано >=1 изображение
    ├── video/               # создаётся только если скачано >=1 видео
    ├── metadata_*.json      # или metadata.json при --overwrite-metadata
    └── report_*.json
```

## Формат отчёта (`report_*.json`)

Отчёт использует snake_case поля:

```json
{
  "username": "example",
  "generated_at": "2026-05-04T15:30:00",
  "media_type": "all",
  "source_mode": "username_query",
  "counters": {
    "downloaded": 10,
    "skipped": 2,
    "failed": 0
  },
  "items": [
    {
      "id": 123456,
      "status": "downloaded",
      "reason": null,
      "url": "https://...",
      "file_path": "output/example/images/123456.jpg",
      "content_type": "image",
      "size_bytes": 1048576,
      "duration_ms": 250
    }
  ]
}
```

Поля элемента отчёта:

- `status` - `downloaded|skipped|failed`
- `reason`
- `url`
- `file_path`
- `content_type`
- `size_bytes`
- `duration_ms`

Дополнительно:

- `source_mode`:
  - `username_query` - использован обычный запрос по `username`;
  - `author_id_query` - сработал fallback по `author_id`.

## Примеры

```powershell
# Только изображения (по умолчанию)
python .\civitai_gallery_downloader.py USERNAME --media-type image

# Только видео
python .\civitai_gallery_downloader.py USERNAME --media-type video --max-downloads 10

# Все типы
python .\civitai_gallery_downloader.py USERNAME --media-type all --max-pages 2 --max-items 20
```

## Примечание

Скрипт использует публичный эндпоинт `GET /api/v1/images` и рассчитан на аккуратную работу с задержками между запросами.

## UI MVP (Browser)

### Установка зависимостей для UI

```powershell
pip install fastapi uvicorn tqdm
```

### Запуск UI

Вариант 1:

```powershell
python .\app.py
```

Вариант 2:

```powershell
uvicorn app:app --reload
```

### Открыть в браузере

`http://127.0.0.1:8000`

### Что есть в UI

- Поля: `username_or_url`, `media_type`, `output_dir`, `max_pages`, `max_items`, `max_downloads`
- Флаги: `metadata_only`, `fallback_author_id`, `no_progress`
- Кнопка `Start`
- Статус выполнения: `running/success/error`
- Результат: путь к папке пользователя и путь к `report_*.json`

### Пример использования

1. Открыть UI
2. Вставить:
   - `https://civitai.com/user/NexBlend/images` или
   - `https://civitai.com/user/NexBlend/videos`
3. Нажать `Start`
4. Дождаться статуса `success` и проверить пути `output_path`/`report_path`

## Baseline и автотесты (pre-UI)

Зафиксирован baseline: `BASELINE.md`.

Локальный прогон автотестов:

```powershell
python -m unittest -v .\test_downloader_core.py
```

Покрытые критичные кейсы:

- default `--media-type` (image);
- fallback `username -> author_id`;
- лимиты `--max-downloads` + `skipped.reason`;
- создание `images/` и `video/` по факту скачивания.

## Текущий статус (фиксировано 2026-05-04)

Подтверждено по результатам задач 7-10:

- CLI сценарии `image|video|all` работают корректно.
- Fallback-механизм `username -> author_id` реализован и проверен отдельными тестами.
- Отчёты `report_*.json` формируются в snake_case формате.
- UI MVP (FastAPI) работает в браузере и возвращает итоговые поля результата.
- Добавлен Playwright smoke (`ui_smoke_playwright.py`) с сохранением скриншотов и API-артефактов.
- Добавлен baseline-документ `BASELINE.md` и автотесты `test_downloader_core.py`.

Артефакты smoke-прогонов и фоновых запусков:

- `./logs/` (bg-runner job logs)
- `./logs/ui-smoke/<timestamp>/` (screenshots, summary.json, ui_server.log)

## USER_GUIDE

Пользовательское пошаговое руководство вынесено в отдельный файл:

- `USER_GUIDE.md`

