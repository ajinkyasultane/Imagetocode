from pathlib import Path
import json, zipfile, shutil
from PIL import Image

from core.detect import detect
from codegen.registry import registry
from utils.io_helpers import make_zip_from_dir

def test_e2e_sample_to_three_zips(tmp_path: Path):
    for screen in ["login","signup","profile"]:
        img_path = Path(f"samples/inputs/{screen}.png")
        assert img_path.exists()
        pil = Image.open(img_path).convert("RGB")
        logs = []
        ir = detect(pil, logs)

        for target in ["web","react","flutter"]:
            gen = registry.get(target); assert gen
            out_dir = tmp_path / f"{screen}_{target}"
            gen(ir, out_dir)
            zip_path = tmp_path / f"{screen}_{target}.zip"
            make_zip_from_dir(out_dir, zip_path)
            assert zip_path.exists() and zip_path.stat().st_size > 0
            with zipfile.ZipFile(zip_path, "r") as zf:
                assert len(zf.namelist()) > 0
