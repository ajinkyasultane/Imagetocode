from PIL import Image
from pathlib import Path
from core.ocr import get_text_lines, ocr_available

def test_ocr_optional_does_not_crash():
    p = Path("samples/inputs/login.png")
    img = Image.open(p).convert("RGB")
    lines = get_text_lines(img)
    assert isinstance(lines, list)
    # Whether or not OCR is available, function should return list
    for item in lines:
        assert isinstance(item, tuple) and len(item) == 3
