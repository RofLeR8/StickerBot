import os
import pytest
from pathlib import Path
from PIL import Image
from unittest.mock import patch
from src.image.utils import resize_image, remove_background
from io import BytesIO

MAX_STICKER_SIZE = [512, 512]


@pytest.fixture
def simple_image():
    """Create temp PNG-image for tests"""
    img = Image.new("RGB", (800,600), color="red")
    return img

def test_resize_image(tmp_path, simple_image):
    input_file = tmp_path / "input.png"
    output_file = tmp_path / "output.png"

    simple_image.save(input_file, format="PNG")
    resize_image(str(input_file), str(output_file))
    
    assert output_file.exists()

    with Image.open(output_file) as img:
        assert img.mode == "RGBA"
        assert img.size[0] <= MAX_STICKER_SIZE[0]
        assert img.size[1] <= MAX_STICKER_SIZE[1]
        assert img.size == (512, 384) # 800x600 -> 512x384


@patch("src.image.utils.remove")
def test_remove_background(mock_remove, tmp_path):
    input_file = tmp_path / "test.png"
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    img.save(input_file, format="PNG")

    mock_result_img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    buf = BytesIO()
    mock_result_img.save(buf, format="PNG")
    mock_remove.return_value = buf.getvalue()

    remove_background(str(input_file))
    with Image.open(input_file) as result:
        assert result.mode == "RGBA"
        assert result.getpixel((0, 0)) == (0, 0, 0, 0)

    mock_remove.assert_called_once()
    args, _ = mock_remove.call_args
    assert isinstance(args[0], bytes)

       