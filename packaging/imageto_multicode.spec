# PyInstaller spec for ImageToMulticode CLI (optional Windows packaging)
# Usage (Windows PowerShell):
#   pyinstaller packaging/imageto_multicode.spec
# Output: dist/im2multi/im2multi.exe

block_cipher = None

a = Analysis(
    ['scripts/cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('codegen/templates/web/*', 'codegen/templates/web'),
        ('codegen/templates/react/*', 'codegen/templates/react'),
        ('codegen/templates/flutter/*', 'codegen/templates/flutter'),
        ('core/schema/ir_schema_v1.json', 'core/schema'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='im2multi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='im2multi')
