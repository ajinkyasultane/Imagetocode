from __future__ import annotations
from typing import List, Tuple
import shutil

try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover - optional dep
    pytesseract = None
    Image = None  # type: ignore

def ocr_available() -> bool:
    return shutil.which("tesseract") is not None and pytesseract is not None and Image is not None

def get_text_lines(pil_img) -> List[Tuple[str, float, Tuple[int,int,int,int]]]:
    """Return list of (text, confidence[0..1], bbox[x1,y1,x2,y2]).
    Degrades gracefully if Tesseract not available.
    """
    if not ocr_available():
        return []
    try:
        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT, lang="eng")
        n = len(data.get("text", []))
        out: List[Tuple[str, float, Tuple[int,int,int,int]]] = []
        for i in range(n):
            txt = (data["text"][i] or "").strip()
            if not txt:
                continue
            conf = data.get("conf", ["-1"]*n)[i]
            try:
                c = float(conf) / 100.0
            except Exception:
                c = 0.0
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            out.append((txt, c, (x, y, x+w, y+h)))
        return out
    except Exception:
        return []
