from __future__ import annotations
from typing import List, Tuple, Sequence
from PIL import Image, ImageDraw, ImageFont

def draw_boxes(img: Image.Image, boxes: List[Tuple[Sequence[float], str, float]]):
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    for bbox, label, score in boxes:
        x1,y1,x2,y2 = bbox
        draw.rectangle((x1,y1,x2,y2), outline="red", width=2)
        text = f"{label}:{score:.2f}" if score is not None else label
        tw, th = draw.textlength(text, font=font), 12
        draw.rectangle((x1, y1-14, x1+tw+6, y1), fill="red")
        draw.text((x1+3, y1-12), text, fill="white", font=font)
    return img
