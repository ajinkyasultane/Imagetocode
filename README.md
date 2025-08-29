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
# Detect UI elements
python scripts/cli.py detect --in samples/inputs/login.png --out samples/ir/login.json --verbose

# Generate code and create ZIP
python scripts/cli.py gen --ir samples/ir/login.json --target web --out outputs/login_web.zip

# Generate code and open directly in IDE
python scripts/cli.py gen --ir samples/ir/login.json --target react --out outputs/login_react.zip --open-ide

# Generate code and open in specific IDE
python scripts/cli.py gen --ir samples/ir/login.json --target flutter --out outputs/login_flutter.zip --open-ide --ide vscode

# List available IDEs
python scripts/cli.py list-ides
```

Targets: `web | react | flutter`.

### IDE Integration

The tool now supports direct IDE integration! After generating code, you can:

**Supported IDEs:**
- **VS Code** (`vscode`) - supports web, react, flutter
- **WebStorm** (`webstorm`) - supports web, react  
- **Android Studio** (`android_studio`) - supports flutter
- **IntelliJ IDEA** (`intellij`) - supports web, react, flutter
- **Sublime Text** (`sublime`) - supports all frameworks
- **Atom** (`atom`) - supports all frameworks

**CLI Options:**
- `--open-ide` - Auto-detect and open in compatible IDE
- `--ide <ide_key>` - Open in specific IDE (vscode, webstorm, etc.)
- `--no-zip` - Skip ZIP creation, only generate project directory
- `list-ides` - Show available IDEs and their capabilities

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
