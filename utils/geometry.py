from __future__ import annotations
from typing import Sequence, Tuple, List

BBox = Tuple[float, float, float, float]

def aspect_ratio(bbox: Sequence[float]) -> float:
    x1, y1, x2, y2 = bbox
    w = max(1e-6, x2 - x1)
    h = max(1e-6, y2 - y1)
    return w / h

def iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, (ax2 - ax1)) * max(0.0, (ay2 - ay1))
    area_b = max(0.0, (bx2 - bx1)) * max(0.0, (by2 - by1))
    union = area_a + area_b - inter + 1e-9
    return inter / union

def clamp_bbox(bbox: Sequence[float], w: float, h: float) -> BBox:
    x1, y1, x2, y2 = bbox
    x1 = max(0.0, min(x1, w)); y1 = max(0.0, min(y1, h))
    x2 = max(0.0, min(x2, w)); y2 = max(0.0, min(y2, h))
    if x2 < x1: x1, x2 = x2, x1
    if y2 < y1: y1, y2 = y2, y1
    return (x1, y1, x2, y2)

def expand(b: Sequence[float], pad: float) -> BBox:
    x1,y1,x2,y2 = b
    return (x1-pad, y1-pad, x2+pad, y2+pad)

def union(a: Sequence[float], b: Sequence[float]) -> BBox:
    ax1,ay1,ax2,ay2 = a
    bx1,by1,bx2,by2 = b
    return (min(ax1,bx1), min(ay1,by1), max(ax2,bx2), max(ay2,by2))

def merge_lines(lines: List[Sequence[float]], max_v_gap: float=6.0) -> List[BBox]:
    """Merge nearby horizontal text lines by vertical proximity."""
    if not lines: return []
    lines = sorted(lines, key=lambda b: (b[1], b[0]))
    merged: List[BBox] = [tuple(lines[0])]  # type: ignore
    for b in lines[1:]:
        x1,y1,x2,y2 = b
        px1,py1,px2,py2 = merged[-1]
        if abs(y1 - py1) <= max_v_gap:
            merged[-1] = (min(px1,x1), min(py1,y1), max(px2,x2), max(py2,y2))
        else:
            merged.append((x1,y1,x2,y2))
    return merged
