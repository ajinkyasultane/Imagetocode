# Windows EXE (Optional)

Build a single-folder CLI `im2multi.exe` using PyInstaller.

## Steps
1. Install Python 3.10+ and Git.
2. In PowerShell:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install pyinstaller
   pyinstaller packaging/imageto_multicode.spec
   ```
3. Your executable will be in `dist/im2multi/`.
4. Test:
   ```powershell
   .\dist\im2multi\im2multi.exe gen --ir samples\ir\login.json --target web --out outputs\login_web.zip
   ```

Notes:
- OCR, Node, Flutter are optional and not bundled.
- Templates and schema are collected via the spec file.
