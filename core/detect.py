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
    "preprocess": {"grayscale": True, "denoise": "bilateral", "threshold": "adaptive", "deskew": False},
    "classify_rules": {
        "input":  {"aspect_min": 2.0, "aspect_max": 12.0},
        "button": {"aspect_min": 1.2, "aspect_max": 8.0},
        "text": {"aspect_min": 1.5, "aspect_max": 15.0},
        "container": {"min_area": 5000},
    },
    "label_to_input": {"min_horizontal_overlap_ratio": 0.4, "max_vertical_gap_ratio_of_input_h": 0.5},
    "grid": {"grid": "12-col", "container_max_width_px": 480, "margin_px": 24},
    "ocr": {"min_conf": 0.40},  # Lower confidence threshold for better text detection
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

def _find_rects(thr: np.ndarray, img_bgr: np.ndarray) -> List[Tuple[int,int,int,int]]:
    # Enhanced contour detection for better UI element recognition
    rects = []
    
    # Method 1: Traditional contour detection
    cnts, _ = cv2.findContours(255 - thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w*h < 400:  # Lower threshold for smaller elements
            continue
        rects.append((x,y,x+w,y+h))
    
    # Method 2: Edge-based detection for modern UI elements
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Dilate edges to connect nearby elements
    kernel = np.ones((3,3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    # Find contours from edges
    edge_cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in edge_cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w*h < 500 or w < 20 or h < 15:  # Filter very small elements
            continue
        rects.append((x,y,x+w,y+h))
    
    # Method 3: Color-based segmentation for distinct UI elements
    try:
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        
        # Detect colored regions (buttons, highlights, etc.)
        # Green elements (like buttons in your design)
        green_lower = np.array([40, 30, 30])
        green_upper = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        # Blue elements
        blue_lower = np.array([100, 30, 30])
        blue_upper = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
        
        # Combine color masks
        color_mask = cv2.bitwise_or(green_mask, blue_mask)
        color_cnts, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for c in color_cnts:
            x, y, w, h = cv2.boundingRect(c)
            if w*h < 200:  # Even smaller threshold for colored elements
                continue
            rects.append((x,y,x+w,y+h))
    except Exception:
        pass  # Color detection is optional
    
    # Remove duplicates and overlapping rectangles
    if not rects:
        return []
        
    rects = list(set(rects))
    filtered_rects = []
    for rect in rects:
        x1, y1, x2, y2 = rect
        # Ensure valid rectangle
        if x2 <= x1 or y2 <= y1:
            continue
            
        is_duplicate = False
        for existing in filtered_rects:
            ex1, ey1, ex2, ey2 = existing
            # Check for significant overlap
            overlap_area = max(0, min(x2, ex2) - max(x1, ex1)) * max(0, min(y2, ey2) - max(y1, ey1))
            rect_area = (x2-x1) * (y2-y1)
            if rect_area > 0 and overlap_area > 0.7 * rect_area:  # 70% overlap threshold
                is_duplicate = True
                break
        if not is_duplicate:
            filtered_rects.append(rect)
    
    return filtered_rects

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

    rects = _find_rects(thr, img_bgr)
    logs.append({"stage": "contours", "count": len(rects)})

    # OCR (optional)
    ocr_lines = get_text_lines(pil_img) if ocr_available() else []
    logs.append({"stage": "ocr", "available": bool(ocr_available()), "lines": len(ocr_lines)})

    elements: List[Dict] = []
    # Enhanced classification with better heuristics
    for i, (x1,y1,x2,y2) in enumerate(rects):
        ar = aspect_ratio((x1,y1,x2,y2))
        w = x2-x1; h = y2-y1
        area = w * h
        
        # Extract region for color analysis
        region = None
        try:
            if (y1 < y2 and x1 < x2 and 
                y1 >= 0 and x1 >= 0 and 
                y2 <= img_bgr.shape[0] and x2 <= img_bgr.shape[1]):
                region = img_bgr[y1:y2, x1:x2]
        except Exception:
            region = None
        
        typ = None
        # Input field detection (rectangular, moderate aspect ratio)
        if (CFG["classify_rules"]["input"]["aspect_min"] <= ar <= CFG["classify_rules"]["input"]["aspect_max"] and 
            20 <= h <= 80 and w >= 100):
            typ = "input"
        # Button detection (moderate aspect ratio, specific size range)
        elif (CFG["classify_rules"]["button"]["aspect_min"] <= ar <= CFG["classify_rules"]["button"]["aspect_max"] and 
              25 <= h <= 100 and w >= 60):
            typ = "button"
        # Logo/icon detection (square-ish, medium size)
        elif 0.5 <= ar <= 2.0 and 50 <= min(w,h) <= 200 and area >= 2500:
            typ = "image"
        # Container detection (large areas)
        elif area >= 10000:
            typ = "container"
        # Text block detection (wide, short)
        elif ar >= 3.0 and h <= 50:
            typ = "text"
        else:
            typ = "container"  # Default to container for unknown elements
            
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
