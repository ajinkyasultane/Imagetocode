from pathlib import Path
import json
from utils.io_helpers import load_ir, save_ir, ir_to_rows, rows_to_ir, autosuffix_if_exists

def test_roundtrip_save_load(tmp_path: Path):
    ir_path = Path("samples/ir/login.json")
    ir = load_ir(ir_path)
    out = tmp_path / "copy.json"
    save_ir(ir, out)
    ir2 = load_ir(out)
    assert ir2["meta"] == ir["meta"]
    assert len(ir2["elements"]) == len(ir["elements"])

def test_rows_to_ir_and_back():
    ir = load_ir(Path("samples/ir/login.json"))
    rows = ir_to_rows(ir)
    rebuilt = rows_to_ir(rows, meta=ir["meta"])
    assert len(rebuilt["elements"]) == len(ir["elements"])
    # ids should match set-wise
    assert set(e["id"] for e in rebuilt["elements"]) == set(e["id"] for e in ir["elements"])

def test_autosuffix_if_exists(tmp_path: Path):
    p = tmp_path / "file.json"
    p.write_text("x")
    p2 = autosuffix_if_exists(p)
    assert p2 != p
    assert p2.name.startswith("file_")
