# ImageToMulticode — Part 1/5 (Core Scaffold)

**Date:** 2025-08-28

This is Part 1 of a five-part build. You get the full repo scaffold, offline-ready, with a working
Streamlit shell, IR schema, CI, and Docker. Detection, IR editor, and generators arrive in Parts 2–4.

## Quickstart (Local)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Docker

```bash
docker build -t imagetomulticode:part1 .
docker run -it --rm -p 8501:8501 imagetomulticode:part1
```

Open: http://localhost:8501

## Repo Layout (Part 1)

- `app.py` — Streamlit app with tabs (Upload, Detect, IR Editor, Generate, Logs, About)
- `core/schema/ir_schema_v1.json` — IR schema contract
- `utils/*` — helpers (EXIF strip, sanitize, geometry/viz stubs)
- `codegen/registry.py` — generator registry (placeholders for now)
- `scripts/cli.py` — CLI skeleton
- `tests/test_bootstrap.py` — smoke tests
- `Dockerfile`, `.github/workflows/ci.yml` — packaging and CI
- `requirements*.txt`, `pyproject.toml` — pinned deps and tool configs

## Notes

- Upload limit is 12 MB; EXIF is stripped on save.
- OCR (Tesseract) is optional; app should continue without it.
- Everything is offline-capable.


## CLI Usage

```bash
python scripts/cli.py detect --in samples/inputs/login.png --out samples/ir/login.json --verbose
python scripts/cli.py gen --ir samples/ir/login.json --target web --out outputs/login_web.zip
```

Targets: `web | react | flutter`.

## Troubleshooting

- **OCR missing**: OK — detection still works (text via OCR will be empty).
- **Node/Flutter missing**: Generators still produce code, build/analyze are optional.
- **Streamlit fails to open**: Ensure port 8501 is free or change with `--server.port`.

## FAQ

**Q:** Does it need internet?  
**A:** No. Everything runs offline after installing requirements.

**Q:** Are outputs deterministic?  
**A:** Yes. Golden snapshots enforce byte-for-byte consistency.

**Q:** How do I build a Windows EXE?  
**A:** See `docs/Windows_EXE.md`.
