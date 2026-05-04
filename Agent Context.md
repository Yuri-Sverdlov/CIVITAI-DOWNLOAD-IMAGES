# Agent Context

## Задание 1

Создать новый проект для скачивания контента с Civitai с поддержкой изображений и видео.

### Цели

1. Реализовать базовый рабочий инструмент для загрузки медиа по данным Civitai API.
2. Поддержать как минимум форматы изображений и видео (включая `mp4`, `webm`).
3. Сделать понятный CLI (и при необходимости API), чтобы можно было ограничивать объём скачивания.
4. Обеспечить устойчивость: таймауты, обработка ошибок, отчёт о скачанных и пропущенных файлах.
5. Подготовить документацию по запуску и примерам использования.

### Организация работы

1. Основной агент ведёт архитектуру, интеграцию и финальную проверку.
2. Второй агент получает подзадачи (кодинг, рефакторинг, поиск багов), результаты встраиваются в общий проект.

## Задание 2

Расширить проект `G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES` для поддержки скачивания видео вместе с картинками.

### Что сделать

1. Расширить текущий downloader (без нового endpoint), добавить CLI-флаг:
   `--media-type image|video|all`
   По умолчанию: `image` (обратная совместимость).
2. Добавить детальный JSON-отчёт:
   `report_<timestamp>.json`
   Для каждого элемента фиксировать:
   - `status`: `downloaded|skipped|failed`
   - `reason`
   - `url`
   - `file_path`
   - `content_type`
   - `size_bytes`
   - `duration_ms`
   И итоговые counters: `downloaded/skipped/failed`.
3. Добавить прогресс-бар через `tqdm`:
   - включать автоматически в TTY;
   - флаг `--no-progress` отключает прогресс.
4. Поддержка видео-форматов минимум:
   `mp4`, `webm`
   (изображения оставить как есть).
5. Обновить README:
   - новый флаг `--media-type`;
   - примеры для `image/video/all`;
   - описание JSON-отчёта и `--no-progress`.

### Требования

1. Не ломать существующий режим `metadata-only`.
2. Не удалять текущую логику пагинации/ограничений.
3. Сделать чистый рефакторинг без дублирования.
4. В финале дать список изменённых файлов и короткий changelog.

## Задание 3

Задание по итогам аудита.

Работать только в проекте:
`G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES`

### Важно

1. Не трогать подпроект `COMFYUI-API-CHAT` (это отдельная зона).
2. Менять только:
   - `civitai_gallery_downloader.py`
   - `README.md`

### Цель

Довести root-скрипт до ТЗ из Задания 2, потому что оно сейчас не реализовано полностью.

### Нужно реализовать

1. CLI-флаг media type:
   - добавить `--media-type image|video|all`;
   - по умолчанию `image` (обратная совместимость);
   - фильтровать элементы по `item.type` из Civitai API:
     - `image` -> только image;
     - `video` -> только video;
     - `all` -> оба типа.
2. Поддержка форматов видео:
   - минимум `mp4`, `webm`, `mov`;
   - корректно сохранять расширение файла по `URL/mimeType/type`;
   - не ломать текущую загрузку изображений.
3. Детальный JSON-отчёт:
   - создавать `report_<timestamp>.json` в `output-dir`;
   - для каждого обработанного элемента сохранять:
     - `status`: `downloaded|skipped|failed`
     - `reason`
     - `url`
     - `file_path`
     - `content_type`
     - `size_bytes`
     - `duration_ms`
   - добавить итоговые counters: `downloaded/skipped/failed`.
4. Прогресс-бар:
   - добавить `tqdm`;
   - показывать при TTY;
   - флаг `--no-progress` полностью отключает прогресс.
5. Совместимость:
   - не сломать `--metadata-only`;
   - не сломать `--max-pages`, `--max-items`, `--max-downloads`, `page/download delays`.
6. README:
   - обновить документацию по `--media-type` и `--no-progress`;
   - добавить примеры запуска для `image/video/all`;
   - добавить описание JSON report.

### Проверка перед сдачей

1. Запустить минимум 2 тестовых прогона:
   - `metadata-only`;
   - реальная загрузка с `media-type=video` и/или `all`.
2. В отчёте показать команды и краткий результат.

### Финальный ответ

1. Список изменённых файлов.
2. Короткий changelog.
3. Подтверждение, что `COMFYUI-API-CHAT` не изменялся.
4. Риски и что осталось на потом (если есть).

## Задание 5

ТЗ на исправление всех выявленных расхождений (для нового агента).

### Область работы

1. Работать только в проекте `G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES`.
2. Изменять только:
   - `civitai_gallery_downloader.py`
   - `README.md`
3. Подпроект `COMFYUI-API-CHAT` не трогать.

### Что нужно исправить

1. Привести поведение `--metadata-only` к ТЗ:
   - в режиме `--metadata-only` обязательно создавать и `metadata`, и `report_<timestamp>.json`;
   - при этом медиа-файлы и медиа-папки не создавать.

2. Поддержать входные форматы автора:
   - как раньше: `USERNAME` (позиционный аргумент);
   - и URL автора:
     - `https://civitai.com/user/<username>/images`
     - `https://civitai.com/user/<username>/videos`
   - из URL корректно извлекать `<username>`.

3. Уточнить логику фильтрации:
   - `--media-type image|video|all` работает и для `USERNAME`, и для URL автора;
   - при URL `/videos` по умолчанию не ломать явный `--media-type`;
   - если `--media-type` не передан, оставить дефолт `image` (обратная совместимость).

4. Привести схему отчёта к единому формату полей (snake_case):
   - `status`
   - `reason`
   - `url`
   - `file_path`
   - `content_type`
   - `size_bytes`
   - `duration_ms`
   - плюс итоговые counters.
   Если сейчас используется camelCase, заменить на snake_case.

5. Проверить структуру выходных папок:
   - `<output-dir>/<USERNAME>/`
   - `images/` создавать только если скачано >=1 изображение;
   - `video/` создавать только если скачано >=1 видео.

6. Проверить поддержку видео-форматов:
   - минимум `mp4`, `webm`, `mov`.

7. README обновить строго по факту:
   - вход: `USERNAME` и URL автора `/images`/`/videos`;
   - поведение `--metadata-only`;
   - `--media-type`, `--no-progress`;
   - структура папок;
   - формат отчёта (snake_case поля).

### Обязательная верификация перед сдачей

1. Показать команды и результаты минимум для 4 кейсов:
   - `--metadata-only`
   - `--media-type image`
   - `--media-type video`
   - URL автора `/videos` (или `/images`) с корректным извлечением username.

2. Подтвердить, что `COMFYUI-API-CHAT` не изменялся в рамках этой задачи.

### Формат финального отчёта агента

1. Список изменённых файлов.
2. Что именно исправлено по каждому пункту этого ТЗ.
3. Команды проверок и краткий результат.
4. Остаточные риски (если есть).

## Задание 4

ТЗ Этап 1 (уточнённое, коротко и однозначно)

1. Поддержать вход для страниц автора Civitai:
   - `https://civitai.com/user/<username>/images`
   - `https://civitai.com/user/<username>/videos`
   Из URL извлекать `<username>` как имя целевой папки.

2. Схема сохранения:
   - Корневая папка: `<output-dir>/<USERNAME>/`
   - Внутри создавать:
     - `images/` только если скачано хотя бы 1 изображение
     - `video/` только если скачано хотя бы 1 видео

3. Типы медиа:
   - image: `jpg`, `jpeg`, `png`, `webp`, `gif`
   - video: `mp4`, `webm`, `mov`

4. Фильтрация:
   - Работает флаг `--media-type image|video|all`
   - `image` — скачивать только изображения
   - `video` — только видео
   - `all` — оба типа

5. Совместимость:
   - Не ломать `--metadata-only`, `--max-pages`, `--max-items`, `--max-downloads`, задержки.

6. Отчёт:
   - `report_<timestamp>.json` сохранять в `<output-dir>/<USERNAME>/`
   - В отчёте по каждому элементу: `status/reason/url/file_path/content_type/size_bytes/duration_ms`
   - Добавить итоговые counters.

7. Ограничение этапа:
   - Страницы модели/LoRA (`/models/...`) в Этап 1 не реализовывать (это Этап 2).

## Задание 6

Новое задание: добавить fallback-режим, если API по username возвращает 0, но страница автора существует.

### Проект

`G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES`

### Менять только

1. `civitai_gallery_downloader.py`
2. `README.md`
3. `Agent Report.md` (дописать итог)

### Цель

Устранить кейс, когда у автора на странице есть контент, но API-запрос с username даёт пусто.

### Что сделать

1. Диагностика причины
   - Логировать режим источника данных:
     - `api_mode = "username_query"` (текущий)
     - `api_mode = "author_id_query"` (fallback)
   - Добавить в metadata/report поле `source_mode`.

2. Fallback-логика
   - Если основной запрос `/api/v1/images?username=<username>` вернул 0 items:
     - попробовать получить `author_id` по странице автора:
       - `https://civitai.com/user/<username>/images` или `/videos`
     - затем запросить API по `userId`/`user_id` (что реально поддерживается API; проверить эмпирически).
   - Если fallback дал items > 0, продолжать скачивание как обычно.
   - Если и fallback пустой — оставлять текущую обработку (0 items), без падения.

3. Управление fallback через CLI
   - Добавить флаг: `--fallback-author-id` (bool, default: ON)
   - Добавить флаг отключения: `--no-fallback-author-id`
   - По умолчанию fallback должен быть включен.

4. Совместимость
   - Не ломать:
     - `--metadata-only`
     - `--media-type`
     - `--max-pages`, `--max-items`, `--max-downloads`
     - структуру папок `<output-dir>/<USERNAME>/images|video`
     - snake_case в report

5. README
   - Добавить раздел про fallback:
     - когда активируется
     - как отключить
     - что это решает (кейс: «страница есть, API username пустой»)

6. Обязательная проверка
   - Прогон 1: `Lannfield/images` с fallback ON
   - Прогон 2: тот же запрос с fallback OFF
   - Сравнить:
     - `items count`
     - `downloaded/skipped`
     - `source_mode` в metadata/report

### Формат финального ответа

1. Изменённые файлы
2. Что реализовано
3. Команды проверок и краткий результат
4. Остаточные риски

## Задание 7

Цель: закрыть остаток чек-листа по live-проверке на страницах, где есть фото и видео, и исправить найденные баги.

Сделать в терминале:
1. Прогнать E2E-тесты на:
   - https://civitai.com/user/NexBlend/images
   - https://civitai.com/user/NexBlend/videos
2. Проверить сценарии:
   - default без --media-type (должно работать как image)
   - --media-type image|video|all
   - fallback ON/OFF для Lannfield/images
   - лимиты --max-items и --max-downloads + корректные skipped/reason
3. Проверить ФС-результат:
   - структура <output>/<username>/images и <output>/<username>/video
   - папки создаются по факту наличия соответствующего контента
4. Если есть баги:
   - исправить код
   - повторить тесты до PASS
5. Обновить Agent Report.md:
   - кратко: что подтверждено, что исправлено, какие команды запускались, финальный статус PASS/FAIL.

Ограничения:
- Работать только в G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES.
- Не трогать COMFYUI-API-CHAT.

## Задание 8

Цель: реализовать UI MVP в браузере для текущего CLI civitai_gallery_downloader.py без изменения проверенного baseline-поведения.

Обязательный scope:
1. Web UI (MVP):
   - Поля формы: username_or_url, media_type (image|video|all), output_dir, max_pages, max_items, max_downloads, metadata_only, allback_author_id, 
o_progress.
   - Кнопка Start.
   - Блок статуса выполнения (running/success/error).
   - Блок результатов: путь к итоговой папке пользователя и путь к eport_*.json.
2. Backend:
   - FastAPI-приложение как обёртка над текущей логикой.
   - Не дублировать downloader-логику; переиспользовать существующие функции.
   - Корректная обработка ошибок с понятным сообщением в UI.
3. Совместимость:
   - CLI сценарии из baseline не ломать.
   - BASELINE.md и 	est_downloader_core.py должны оставаться PASS.
4. Документация:
   - Обновить README разделом UI MVP: установка зависимостей, запуск, URL в браузере, пример использования.

Критерии приёмки (Definition of Done):
1. Запуск UI командой вида python .\\app.py или uvicorn app:app --reload.
2. В браузере можно запустить скачивание для:
   - https://civitai.com/user/NexBlend/images
   - https://civitai.com/user/NexBlend/videos
3. После выполнения видны:
   - финальный статус,
   - путь к output,
   - путь к report JSON.
4. Локальные автотесты проходят:
   - python -m unittest -v .\\test_downloader_core.py.
5. Заполнить Agent Report.md:
   - что реализовано,
   - какие файлы изменены,
   - как запускать UI,
   - результаты smoke-проверки.

Ограничения:
- Работать только в G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES.
- Не трогать COMFYUI-API-CHAT.

## Задание 9

Цель: выполнить проверки в режиме видимого прогресса через bg-runner, с обязательными апдейтами каждые 20-30 секунд.

Контекст:
- Проект: G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES
- Использовать bg-runner из: G:\AI\_MY_PROGRAMMING_3\_AGENT-TOOLS\bg-runner
- Работать только в CIVITAI-DOWNLOAD-IMAGES, не трогать COMFYUI-API-CHAT

Требование по коммуникации (обязательно):
- Писать короткий статус каждые 20-30 секунд, даже если процесс ещё идёт.
- В каждом статусе указывать: что запущено, что подтверждено, какой следующий шаг.

Что сделать:
1. Подготовить папку логов в проекте: .\logs.
2. Через bg-runner запустить долгие проверки Task 8 (UI MVP smoke + downloader smoke), чтобы терминал не блокировался.
3. Каждые 20-30 сек присылать обновления со статусом job_id и прогрессом.
4. Если найдены баги: исправить и перезапустить проверку через bg-runner.
5. По завершении обновить Agent Report.md:
   - команды запуска,
   - job_id,
   - итог PASS/FAIL,
   - что исправлено (если было),
   - где смотреть логи.

Критерий готовности:
- Процесс прозрачен (виден живой прогресс каждые 20-30 сек),
- Проверки завершены,
- Agent Report.md обновлён с итогом.

## Задание 10

Цель: автоматизировать UI-проверку через Playwright с визуальной верификацией и циклом исправления багов.

Контекст:
- Проект: G:\AI\_MY_PROGRAMMING_2\CIVITAI-DOWNLOAD-IMAGES
- Разрешено использовать существующий подход/скрипт из COMFYUI-API-CHAT внутри этого проекта как основу.
- Работать только в рамках CIVITAI-DOWNLOAD-IMAGES.

Что сделать:
1. Создать/адаптировать ui_smoke_playwright.py (или эквивалент), который:
   - запускает UI приложения,
   - открывает страницу в браузере,
   - заполняет форму и запускает сценарии:
     - https://civitai.com/user/NexBlend/images
     - https://civitai.com/user/NexBlend/videos
     - https://civitai.com/user/Lannfield/images (fallback ON и отдельно OFF),
   - делает скриншоты ключевых этапов,
   - сохраняет артефакты в ./logs/ui-smoke/.
2. Проверить ожидаемые результаты:
   - статус success в UI/API-ответе,
   - наличие user_output_dir и eport_file,
   - корректные счётчики downloaded/skipped/failed.
3. Если обнаружены баги UI/flow:
   - исправить код,
   - повторить прогон,
   - добиться PASS.
4. Обновить Agent Report.md:
   - команды запуска,
   - где лежат скриншоты/логи,
   - какие баги найдены и как исправлены,
   - финальный статус PASS/FAIL.

Требование по коммуникации:
- Апдейт каждые 20-30 секунд, пока идёт прогон.

Критерии готовности:
- Авто-smoke отрабатывает по всем указанным URL,
- Скриншоты и логи сохранены,
- При наличии багов они исправлены и повторно проверены,
- В Agent Report.md зафиксирован итог.
