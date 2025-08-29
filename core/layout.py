from __future__ import annotations
from typing import Dict, List, Tuple, Sequence

BBox = Tuple[float, float, float, float]

def snap_to_grid(bbox: Sequence[float], grid_cols: int = 12, container_w: float = 480.0, margin: float = 24.0) -> BBox:
    x1, y1, x2, y2 = bbox
    col_w = (container_w - 2*margin) / grid_cols
    def snap_x(x):
        # snap to nearest column boundary
        col = round((x - margin) / col_w)
        return margin + col * col_w
    return (snap_x(x1), y1, snap_x(x2), y2)

def horizontal_overlap_ratio(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, _, ax2, _ = a
    bx1, _, bx2, _ = b
    inter = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    aw = max(1e-6, ax2 - ax1)
    bw = max(1e-6, bx2 - bx1)
    return inter / min(aw, bw)

def associate_label_to_input(labels: List[Dict], inputs: List[Dict], min_overlap: float, max_vgap_ratio: float) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for lbl in labels:
        lx1, ly1, lx2, ly2 = lbl["bbox"]
        lmid_y = (ly1+ly2)/2.0
        best = None
        best_dy = 1e9
        for inp in inputs:
            x1, y1, x2, y2 = inp["bbox"]
            h = max(1e-6, y2 - y1)
            vgap = y1 - ly2  # label above input
            if vgap < 0 or vgap > max_vgap_ratio * h:
                continue
            if horizontal_overlap_ratio(lbl["bbox"], inp["bbox"]) < min_overlap:
                continue
            dy = vgap
            if dy < best_dy:
                best_dy = dy
                best = inp
        if best is not None:
            pairs.append((lbl["id"], best["id"]))
    return pairs
