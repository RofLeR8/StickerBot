import os
import logging
from PIL import Image
from rembg import remove
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

MAX_STICKER_SIZE = [512, 512]

def resize_image(input_path: str, output_path: str) -> None:
    logger.debug("Resizing image from %s to %s", input_path, output_path)
    
    # Создаём директорию, если не существует
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        logger.info("Creating directory: %s", output_dir)
        os.makedirs(output_dir, exist_ok=True)
    
    with Image.open(input_path) as img:
        img = img.convert("RGBA")

        # Получаем текущие размеры
        w, h = img.size
        logger.debug("Original image size: %dx%d", w, h)

        # Определяем масштаб: одна сторона должна быть 512, другая ≤ 512
        if w >= h:
            new_w = 512
            new_h = int(h * (512.0 / w))
        else:
            new_h = 512
            new_w = int(w * (512.0 / h))

        logger.debug("Resized image size: %dx%d", new_w, new_h)

        # Масштабируем (увеличиваем или уменьшаем)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Сохраняем
        img.save(output_path, format="PNG", optimize=True)
        logger.debug("Image saved to %s", output_path)

def remove_background(png_path: str) -> None:
    logger.debug("Removing background from %s", png_path)
    
    with open(png_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    with open(png_path, "wb") as f:
        f.write(output_bytes)
    
    logger.debug("Background removed successfully")


