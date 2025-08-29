from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json

from utils.sanitize import html_escape

THEME = {"primary_color": "#2563EB", "radius_px": 12, "font_stack": "system-ui, Arial"}

def _env():
    tpl_dir = Path(__file__).parent / "templates" / "web"
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env

def _normalized_elements(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    els = []
    for el in ir.get("elements", []):
        style = el.get("style", {}) or {}
        normalized_el = {
            "id": el.get("id", ""),
            "type": el.get("type"),
            "text": el.get("text"),
            "label": el.get("label"),
            "src": el.get("src"),
            "secure": bool(el.get("secure", False)),
            "placeholder": el.get("placeholder"),
            "style": {"role": style.get("role"), "variant": style.get("variant")},
            "bbox": el.get("bbox", [0, 0, 100, 30]),
        }
        
        # Add enhanced visual properties if available
        if "avg_color" in el:
            normalized_el["avg_color"] = el["avg_color"]
        if "dominant_color" in el:
            normalized_el["dominant_color"] = el["dominant_color"]
        if "has_border" in el:
            normalized_el["has_border"] = el["has_border"]
        if "fill_ratio" in el:
            normalized_el["fill_ratio"] = el["fill_ratio"]
        if "is_uniform" in el:
            normalized_el["is_uniform"] = el["is_uniform"]
            
        els.append(normalized_el)
    return els

def generate(ir: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    env = _env()
    meta = ir.get("meta", {})
    
    # Extract background color from enhanced detection if available
    if "layout" in meta and "background" not in meta:
        # Try to get background from color analysis
        colors = meta.get("colors", [])
        if colors:
            # Use the first (most dominant) color as background hint
            meta["layout"] = {"background": {"hex": colors[0]}}
    
    ctx = {"meta": meta, "elements": _normalized_elements(ir), "theme": THEME}
    (out_dir / "index.html").write_text(env.get_template("index.html.j2").render(**ctx), encoding="utf-8")
    (out_dir / "styles.css").write_text(env.get_template("styles.css.j2").render(**ctx), encoding="utf-8")
    (out_dir / "app.js").write_text(env.get_template("app.js.j2").render(), encoding="utf-8")
    (out_dir / "README.md").write_text(env.get_template("README.md.j2").render(), encoding="utf-8")

# Register
from .registry import registry
registry.register("web", generate)
