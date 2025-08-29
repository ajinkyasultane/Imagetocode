from __future__ import annotations
from pathlib import Path
from typing import BinaryIO, Dict, List, Any
from PIL import Image, ImageOps
import io
import re
import zipfile
import json

MAX_UPLOAD_MB = 12
ALLOWED_EXTS = {".png", ".jpg", ".jpeg"}

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")

def safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = _SAFE_NAME_RE.sub("", name)
    if not name:
        name = "file"
    return name[:120]

def autosuffix_if_exists(path: Path) -> Path:
    base = path.with_suffix("")
    ext = path.suffix
    i = 1
    p = path
    while p.exists():
        p = base.with_name(f"{base.name}_{i}").with_suffix(ext)
        i += 1
    return p

def _strip_exif(img: Image.Image) -> Image.Image:
    data = list(img.getdata())
    new_img = Image.new(img.mode, img.size)
    new_img.putdata(data)
    return new_img

def save_uploaded_image_strip_exif(file_obj: BinaryIO, dest: Path) -> Image.Image:
    dest.parent.mkdir(parents=True, exist_ok=True)
    raw = file_obj.read()
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = _strip_exif(img)
    # Always save as PNG to normalize
    img.save(dest, format="PNG")
    return img

def make_zip_from_dir(src_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in src_dir.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(src_dir))

# -------- IR read/write + table conversion (for tests & editor) --------

def load_ir(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data

def save_ir(ir: Dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ir, indent=2), encoding="utf-8")
    return path

IR_COLUMNS = [
    "id","type","bbox","text","label","src","style.role","style.variant","secure","placeholder"
]

def ir_to_rows(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for el in ir.get("elements", []):
        row: Dict[str, Any] = {
            "id": el.get("id",""),
            "type": el.get("type","text"),
            "bbox": ",".join(str(x) for x in el.get("bbox",[0,0,0,0])),
            "text": el.get("text",""),
            "label": el.get("label",""),
            "src": el.get("src",""),
            "style.role": (el.get("style",{}) or {}).get("role",""),
            "style.variant": (el.get("style",{}) or {}).get("variant",""),
            "secure": el.get("secure", False),
            "placeholder": el.get("placeholder",""),
        }
        rows.append(row)
    return rows

def rows_to_ir(rows: List[Dict[str, Any]], meta: Dict[str, Any]) -> Dict[str, Any]:
    els: List[Dict[str, Any]] = []
    for r in rows:
        if not r.get("id"):
            # skip empty rows
            continue
        bbox_str = r.get("bbox","0,0,0,0")
        try:
            parts = [float(x.strip()) for x in bbox_str.split(",")]
        except Exception:
            parts = [0.0,0.0,0.0,0.0]
        style = {}
        if r.get("style.role"): style["role"] = r["style.role"]
        if r.get("style.variant"): style["variant"] = r["style.variant"]
        el: Dict[str, Any] = {
            "id": str(r.get("id")),
            "type": r.get("type","text"),
            "bbox": parts[:4],
        }
        if r.get("text"): el["text"] = r["text"]
        if r.get("label"): el["label"] = r["label"]
        if r.get("src"): el["src"] = r["src"]
        if style: el["style"] = style  # only include if non-empty
        if r.get("secure"): el["secure"] = bool(r["secure"])
        if r.get("placeholder"): el["placeholder"] = r["placeholder"]
        els.append(el)
    return {"meta": meta, "elements": els}
