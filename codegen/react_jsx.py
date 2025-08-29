from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader, select_autoescape

THEME = {"primary_color": "#2563EB", "radius_px": 12, "font_stack": "system-ui, Arial"}

def _env():
    tpl_dir = Path(__file__).parent / "templates" / "react"
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html"]),
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
    # Write structure
    (out_dir / "index.html").write_text(env.get_template("index.html.j2").render(**ctx), encoding="utf-8")
    src = out_dir / "src"
    src.mkdir(exist_ok=True)
    (src / "main.jsx").write_text(env.get_template("src_main.jsx.j2").render(), encoding="utf-8")
    (src / "App.jsx").write_text(env.get_template("src_App.jsx.j2").render(**ctx), encoding="utf-8")
    (out_dir / "index.css").write_text(env.get_template("src_index.css.j2").render(**ctx), encoding="utf-8")
    (out_dir / "package.json").write_text(env.get_template("package.json.j2").render(), encoding="utf-8")
    (out_dir / "README.md").write_text(env.get_template("README.md.j2").render(), encoding="utf-8")

# Register
from .registry import registry
registry.register("react", generate)
