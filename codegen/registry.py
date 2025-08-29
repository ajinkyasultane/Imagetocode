from __future__ import annotations
from typing import Callable, Dict, Optional
from pathlib import Path

class GeneratorRegistry:
    def __init__(self) -> None:
        self._reg: Dict[str, Callable[..., None]] = {}

    def register(self, name: str, fn: Callable[..., None]) -> None:
        self._reg[name] = fn

    def get(self, name: str) -> Optional[Callable[..., None]]:
        return self._reg.get(name)

    def available(self):
        return sorted(self._reg.keys())

registry = GeneratorRegistry()

# Registered in module import side-effects
def _ensure_registration():
    try:
        from . import html_css_js  # noqa: F401
        from . import react_jsx    # noqa: F401
        from . import flutter_dart # noqa: F401
    except Exception:
        pass

_ensure_registration()
