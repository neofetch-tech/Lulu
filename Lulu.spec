# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root_dir = Path(r"C:\Users\ZT_MATADOR\Desktop\Lulu\lulu")
frontend_dist = root_dir / "frontend" / "dist"

datas = [
    (str(frontend_dist), "frontend/dist"),
]

datas.extend(collect_data_files("huggingface_hub"))

binaries = []
hiddenimports = [
    "lulu",
    "lulu.desktop",
    "lulu.desktop.api",
    "lulu.desktop.app",
    "lulu.engine",
    "lulu.registry",
    "webview",
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
    "huggingface_hub",
    "huggingface_hub.utils",
    "clr",
]

block_cipher = None

a = Analysis(
    [str(root_dir / "python" / "lulu" / "desktop" / "app.py")],
    pathex=[str(root_dir / "python")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["webview.platforms.android", "webview.platforms.qt", "webview.platforms.gtk", "webview.platforms.cocoa"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Lulu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'C:\Users\ZT_MATADOR\Desktop\Lulu\lulu\frontend\public\logo.ico',
)
