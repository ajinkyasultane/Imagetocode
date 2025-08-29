from __future__ import annotations
from typing import Dict, List, Tuple
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from utils.geometry import aspect_ratio, iou, clamp_bbox
from core.ocr import get_text_lines, ocr_available
from core.layout import snap_to_grid, associate_label_to_input

# Heuristics config
CFG = {
    "resize_max_side_px": 2048,
    "preprocess": {"grayscale": True, "denoise": "bilateral", "threshold": "adaptive", "deskew": True},
    "classify_rules": {
        "input":  {"aspect_min": 2.0, "aspect_max": 10.0},
        "button": {"aspect_min": 1.5, "aspect_max": 5.0},
    },
    "label_to_input": {"min_horizontal_overlap_ratio": 0.4, "max_vertical_gap_ratio_of_input_h": 0.5},
    "grid": {"grid": "12-col", "container_max_width_px": 480, "margin_px": 24},
    "ocr": {"min_conf": 0.55},
}

def _to_cv(pil_img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def _deskew(gray: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(gray < 250))
    if coords.size == 0:
        return gray
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = gray.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def preprocess(pil_img: Image.Image) -> Tuple[np.ndarray, np.ndarray]:
    img = _to_cv(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    if CFG["preprocess"]["deskew"]:
        gray = _deskew(gray)
    thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    return img, thr

def _find_rects(thr: np.ndarray) -> List[Tuple[int,int,int,int]]:
    # Find contours that look like UI boxes
    cnts, _ = cv2.findContours(255 - thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w*h < 600:  # filter tiny
            continue
        rects.append((x,y,x+w,y+h))
    return rects

def detect(pil_img: Image.Image, logs: List[Dict]) -> Dict:
    W, H = pil_img.size
    logs.append({"stage": "start", "w": W, "h": H})

    # Resize if needed
    max_side = max(W, H)
    if max_side > CFG["resize_max_side_px"]:
        scale = CFG["resize_max_side_px"] / max_side
        pil_img = pil_img.resize((int(W*scale), int(H*scale)))
        W, H = pil_img.size
        logs.append({"stage": "resize", "scale": scale, "w": W, "h": H})

    img_bgr, thr = preprocess(pil_img)
    logs.append({"stage": "preprocess", "thr_shape": thr.shape})

    rects = _find_rects(thr)
    logs.append({"stage": "contours", "count": len(rects)})

    # OCR (optional)
    ocr_lines = get_text_lines(pil_img) if ocr_available() else []
    logs.append({"stage": "ocr", "available": bool(ocr_available()), "lines": len(ocr_lines)})

    elements: List[Dict] = []
    # Classify rects into input/button by aspect ratio; others may be images
    for i, (x1,y1,x2,y2) in enumerate(rects):
        ar = aspect_ratio((x1,y1,x2,y2))
        w = x2-x1; h = y2-y1
        typ = None
        if CFG["classify_rules"]["input"]["aspect_min"] <= ar <= CFG["classify_rules"]["input"]["aspect_max"] and h<=80:
            typ = "input"
        elif CFG["classify_rules"]["button"]["aspect_min"] <= ar <= CFG["classify_rules"]["button"]["aspect_max"] and 40<=h<=100:
            typ = "button"
        else:
            typ = "image"
        elements.append({"id": f"el_{i}", "type": typ, "bbox": [float(x1),float(y1),float(x2),float(y2)]})

    # Use OCR lines as text elements
    for j, (txt, conf, (x1,y1,x2,y2)) in enumerate(ocr_lines):
        if conf < CFG["ocr"]["min_conf"]:
            continue
        elements.append({"id": f"text_{j}", "type": "text", "bbox": [float(x1),float(y1),float(x2),float(y2)], "text": txt})

    # Snap some elements to grid horizontally
    for el in elements:
        el["bbox"] = list(snap_to_grid(el["bbox"], grid_cols=12, container_w=CFG["grid"]["container_max_width_px"], margin=CFG["grid"]["margin_px"]))

    ir = {"meta": {"schema": 1, "title": "auto", "w": float(W), "h": float(H), "grid": CFG["grid"]["grid"]}, "elements": elements}
    return ir
