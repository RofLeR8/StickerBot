import os
from PIL import Image
from rembg import remove
from dotenv import load_dotenv



MAX_STICKER_SIZE = [512, 512]

def resize_image(input_path: str, output_path: str) -> None:
    with Image.open(input_path) as img:
        img = img.convert("RGBA")
        img.thumbnail(MAX_STICKER_SIZE, Image.LANCZOS)
        img.save(output_path, format="PNG")

def remove_background(png_path: str) -> None:
    with open(png_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    with open(png_path, "wb") as f:
        f.write(output_bytes)


