from pathlib import Path
import json
from PIL import Image
from core.detect import detect
from jsonschema import validate

SCHEMA = json.loads(Path("core/schema/ir_schema_v1.json").read_text())

def test_detect_runs_and_validates_on_sample():
    p = Path("samples/inputs/login.png")
    assert p.exists()
    img = Image.open(p).convert("RGB")
    logs = []
    ir = detect(img, logs)
    validate(instance=ir, schema=SCHEMA)
    assert isinstance(ir["elements"], list) and len(ir["elements"]) > 0
    types = set(e["type"] for e in ir["elements"])
    assert {"text","input","button","image"} & types  # at least one type present
