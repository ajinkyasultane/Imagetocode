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
        els.append({
            "id": el.get("id", ""),
            "type": el.get("type"),
            "text": el.get("text"),
            "label": el.get("label"),
            "src": el.get("src"),
            "secure": bool(el.get("secure", False)),
            "placeholder": el.get("placeholder"),
            "style": {"role": style.get("role"), "variant": style.get("variant")},
        })
    return els

def generate(ir: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    env = _env()
    meta = ir.get("meta", {})
    ctx = {"meta": meta, "elements": _normalized_elements(ir), "theme": THEME}
    (out_dir / "index.html").write_text(env.get_template("index.html.j2").render(**ctx), encoding="utf-8")
    (out_dir / "styles.css").write_text(env.get_template("styles.css.j2").render(theme=THEME), encoding="utf-8")
    (out_dir / "app.js").write_text(env.get_template("app.js.j2").render(), encoding="utf-8")
    (out_dir / "README.md").write_text(env.get_template("README.md.j2").render(), encoding="utf-8")

# Register
from .registry import registry
registry.register("web", generate)
