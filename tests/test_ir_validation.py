from pathlib import Path
import json
from jsonschema import validate

SCHEMA = json.loads(Path("core/schema/ir_schema_v1.json").read_text())

def _valid_login():
    return json.loads(Path("samples/ir/login.json").read_text())

def _validate_extra(ir):
    errs = []
    W, H = float(ir["meta"]["w"]), float(ir["meta"]["h"])
    ids = set()
    for el in ir.get("elements", []):
        if el["id"] in ids:
            errs.append(f"dup {el['id']}")
        ids.add(el["id"])
        x1,y1,x2,y2 = el["bbox"]
        if not (0 <= x1 <= W and 0 <= x2 <= W and 0 <= y1 <= H and 0 <= y2 <= H):
            errs.append("oob")
        if x2 < x1 or y2 < y1:
            errs.append("inv")
    return errs

def test_valid_ir_passes_schema_and_bounds():
    ir = _valid_login()
    validate(instance=ir, schema=SCHEMA)
    assert _validate_extra(ir) == []

def test_invalid_ir_detects_duplicate_and_bounds():
    ir = _valid_login()
    # add duplicate id
    ir["elements"].append(dict(ir["elements"][0]))
    # make bbox OOB
    ir["elements"][0]["bbox"] = [-10, -10, 9999, 9999]
    # schema still passes (since schema can't know bounds), but extra check should flag
    validate(instance=ir, schema=SCHEMA)
    errs = _validate_extra(ir)
    assert any("dup" in e for e in errs) and ("oob" in errs or "inv" in errs)
