from __future__ import annotations
import html
import re

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")

def html_escape(text: str) -> str:
    return html.escape(text, quote=True)

def safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = _SAFE_NAME_RE.sub("", name)
    if not name:
        name = "file"
    return name[:120]
