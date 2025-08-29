from __future__ import annotations
import argparse, json, shutil, os
from pathlib import Path
from PIL import Image

from core.detect import detect
from codegen.registry import registry
from utils.io_helpers import make_zip_from_dir

def cmd_detect(args):
    src = Path(args.input)
    out = Path(args.out)
    if not src.exists():
        raise SystemExit(f"Input image not found: {src}")
    pil = Image.open(src).convert("RGB")
    logs = []
    ir = detect(pil, logs)
    if args.no_ocr:
        # remove OCR-derived text elements (heuristic: ids starting with 'text_')
        ir["elements"] = [e for e in ir["elements"] if not (e.get("type") == "text" and str(e.get("id","")).startswith("text_"))]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ir, indent=2), encoding="utf-8")
    if args.verbose:
        print("Logs:", json.dumps(logs, indent=2))
    print(f"Wrote IR → {out}")

def cmd_gen(args):
    ir_path = Path(args.ir)
    target = args.target
    out_zip = Path(args.out)
    if target not in ("web","react","flutter"):
        raise SystemExit("target must be one of: web | react | flutter")
    if not ir_path.exists():
        raise SystemExit(f"IR not found: {ir_path}")
    ir = json.loads(ir_path.read_text(encoding="utf-8"))
    gen = registry.get(target)
    if gen is None:
        raise SystemExit(f"Generator not registered: {target}")
    tmp_out = out_zip.with_suffix("")
    if tmp_out.exists():
        shutil.rmtree(tmp_out)
    gen(ir, tmp_out)
    if out_zip.exists():
        out_zip.unlink()
    make_zip_from_dir(tmp_out, out_zip)
    print(f"Generated {target} → {out_zip}")

def main(argv=None):
    p = argparse.ArgumentParser(prog="im2multi", description="ImageToMulticode CLI")
    sub = p.add_subparsers(dest="cmd")

    p_detect = sub.add_parser("detect", help="Detect UI elements and output IR JSON")
    p_detect.add_argument("--in", dest="input", required=True, help="Input PNG/JPG")
    p_detect.add_argument("--out", dest="out", required=True, help="Output IR JSON path")
    p_detect.add_argument("--no-ocr", action="store_true", help="Disable OCR-derived texts from output")
    p_detect.add_argument("--verbose", action="store_true")
    p_detect.set_defaults(func=cmd_detect)

    p_gen = sub.add_parser("gen", help="Generate code ZIP from IR")
    p_gen.add_argument("--ir", required=True, help="Path to IR JSON")
    p_gen.add_argument("--target", required=True, help="web | react | flutter")
    p_gen.add_argument("--out", required=True, help="Output ZIP path")
    p_gen.set_defaults(func=cmd_gen)

    args = p.parse_args(argv)
    if not hasattr(args, "func"):
        p.print_help()
        return 2
    return args.func(args)

if __name__ == "__main__":
    main()
