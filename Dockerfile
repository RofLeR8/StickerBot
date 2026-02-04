# StickerBot — Telegram-бот для управления стикерпаком
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PHOTO_DIR=/app/data/photos

WORKDIR /app

# Зависимости (без rembg/PIL тяжёлых — можно вынести в multi-stage при необходимости)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY src ./src

# Директории для данных (фото и БД)
RUN mkdir -p /app/data/photos && chmod 755 /app/data /app/data/photos

# Непривилегированный пользователь
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Токен и режим задаются через env при запуске контейнера
# Пример: docker run -e BOT_TOKEN_PROD=... -e DATABASE_URL=... -v stickerbot_data:/app/data ...
ENTRYPOINT ["python", "src/main.py"]
CMD ["--mode", "prod"]
