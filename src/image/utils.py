import os
from PIL import Image
from rembg import remove
from dotenv import load_dotenv



MAX_STICKER_SIZE = [512, 512]

def resize_image(input_path: str, output_path: str) -> None:
    with Image.open(input_path) as img:
        img = img.convert("RGBA")

        # Получаем текущие размеры
        w, h = img.size

        # Определяем масштаб: одна сторона должна быть 512, другая ≤ 512
        if w >= h:
            new_w = 512
            new_h = int(h * (512.0 / w))
        else:
            new_h = 512
            new_w = int(w * (512.0 / h))

        # Масштабируем (увеличиваем или уменьшаем)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Сохраняем
        img.save(output_path, format="PNG", optimize=True)

def remove_background(png_path: str) -> None:
    with open(png_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    with open(png_path, "wb") as f:
        f.write(output_bytes)


