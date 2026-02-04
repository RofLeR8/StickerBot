# StickerBot

Telegram-бот для управления стикерпаком (добавление/удаление стикеров, заявки на доступ, админ-панель).

## Запуск в Docker

Сборка образа:

```bash
docker build -t stickerbot .
```

Запуск (токен и БД задаются переменными окружения, данные — volume):

```bash
docker run -d --name stickerbot \
  -e BOT_TOKEN_PROD="YOUR_BOT_TOKEN" \
  -e DATABASE_URL="sqlite+aiosqlite:////app/data/stickerbot.db" \
  -e PHOTO_DIR="/app/data/photos" \
  -e STICKER_SET_NAME="your_sticker_set_name" \
  -v stickerbot_data:/app/data \
  stickerbot
```

Режим `dev`:

```bash
docker run -d --name stickerbot \
  -e BOT_TOKEN_DEV="YOUR_DEV_TOKEN" \
  -e DATABASE_URL="sqlite+aiosqlite:////app/data/stickerbot.db" \
  -e PHOTO_DIR="/app/data/photos" \
  -v stickerbot_data:/app/data \
  stickerbot --mode dev
```

Для SQLite в Docker нужен драйвер `aiosqlite` — добавьте его в `requirements.txt` при использовании SQLite.

## Тесты

Установка зависимостей для тестов:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Запуск тестов (из корня проекта, в `PYTHONPATH` должен быть каталог `src`):

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

или через pytest.ini (указан `pythonpath = src .`):

```bash
pytest
```

- **test_image_utils.py** — обработка изображений (resize, remove_background).
- **test_database_crud.py** — CRUD пользователей и операций (async, in-memory SQLite).
- **test_models.py** — валидация Pydantic-схем.
- **test_keyboards.py** — наличие кнопок и тип клавиатур.

Для async-тестов нужны `pytest-asyncio` и `aiosqlite` (см. `requirements-dev.txt`).
