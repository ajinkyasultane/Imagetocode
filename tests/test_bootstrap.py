from pathlib import Path
import json
import importlib

def test_schema_exists_and_loads():
    path = Path("core/schema/ir_schema_v1.json")
    assert path.exists(), "Schema file missing"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "meta" in data and "elements" in data

def test_app_import_and_tabs():
    app = importlib.import_module("app")
    assert hasattr(app, "APP_TABS")
    assert app.APP_TABS == ["Upload", "Detect", "IR Editor", "Generate", "Logs", "About"]

def test_repo_files_present():
    for p in ["Dockerfile", "README.md", "requirements.txt"]:
        assert Path(p).exists(), f"Missing {{p}}"
