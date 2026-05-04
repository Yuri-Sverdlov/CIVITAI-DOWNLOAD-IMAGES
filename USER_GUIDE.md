# USER GUIDE

Краткое руководство для запуска и проверки `CIVITAI-DOWNLOAD-IMAGES`.

## 1. Что делает проект

Проект скачивает изображения и/или видео с Civitai по `username` или URL автора, сохраняет метаданные и формирует отчёт.

## 2. Быстрый старт (CLI)

```powershell
cd G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES
python .\civitai_gallery_downloader.py "https://civitai.com/user/NexBlend/images" --media-type all --max-pages 1 --max-downloads 3 --output-dir G:\tmp\civitai_quickstart --no-progress
```

Проверить результат:

- `G:\tmp\civitai_quickstart\NexBlend\images`
- `G:\tmp\civitai_quickstart\NexBlend\video`
- `report_*.json`

## 3. Быстрый старт (UI в браузере)

Запуск:

```powershell
cd G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES
python .\app.py
```

Открыть:

- `http://127.0.0.1:8000`

Минимальная проверка:

1. Вставить URL автора (например, `NexBlend/images` или `NexBlend/videos`).
2. Выбрать `media_type`.
3. Нажать `Start`.
4. Дождаться `success`.
5. Проверить `user_output_dir` и `report_file`.

## 4. Как читать результат

Главные поля ответа/отчёта:

- `status`: `success` или `error`
- `source_mode`: `username_query` или `author_id_query`
- `downloaded`, `skipped`, `failed`
- `report_file`

## 5. Типовые проблемы

- Ноль файлов при видимом контенте на странице:
  - проверить `fallback_author_id` (ON)
  - проверить URL формата `/user/<name>/images` или `/videos`
- Нет папки `video`:
  - папка создаётся только если реально скачалось хотя бы одно видео
- Долгий прогон:
  - запускать через `bg-runner` и смотреть прогресс через `status.py`

## 6. Что дальше (будет расширено)

- Подробный сценарий UAT по шагам
- Расширенная таблица ошибок и решений
- Примеры для тематических страниц/моделей
- Режим автоматического UI smoke с Playwright
