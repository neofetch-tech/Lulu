"""
PyInstaller build script to package Lulu into a standalone Windows .exe executable.

Usage:
    python build_exe.py
"""

import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent.resolve()
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
BUILD_DIR = ROOT_DIR / "build"
DIST_DIR = ROOT_DIR / "dist"


def check_prerequisites():
    print("[+] Checking prerequisites...")
    if not FRONTEND_DIST.exists() or not (FRONTEND_DIST / "index.html").exists():
        print("[+] Building React frontend...")
        subprocess.check_call(["npm", "run", "build"], cwd=str(ROOT_DIR / "frontend"), shell=True)

    try:
        import PyInstaller
        import PIL
    except ImportError:
        print("[+] Installing PyInstaller and Pillow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pillow"])


def ensure_ico_icon() -> str | None:
    png_path = ROOT_DIR / "frontend" / "public" / "logo.png"
    ico_path = ROOT_DIR / "frontend" / "public" / "logo.ico"

    if png_path.exists():
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"[OK] Minimalist logo converted to ICO: {ico_path}")
            return str(ico_path)
        except Exception as e:
            print(f"[!] Could not convert PNG to ICO: {e}")

    return str(ico_path) if ico_path.exists() else None


def create_spec_file() -> Path:
    icon_path = ensure_ico_icon()
    icon_str = f"r'{icon_path}'" if icon_path else "None"

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root_dir = Path(r"{ROOT_DIR}")
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
    hooksconfig={{}},
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
    icon={icon_str},
)
"""
    spec_path = ROOT_DIR / "Lulu.spec"
    spec_path.write_text(spec_content, encoding="utf-8")
    print(f"[OK] Generated PyInstaller spec: {spec_path}")
    return spec_path


def build():
    check_prerequisites()
    spec_path = create_spec_file()

    print("[BUILD] Compiling standalone Lulu.exe with PyInstaller...")
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        str(spec_path)
    ], cwd=str(ROOT_DIR))

    exe_path = DIST_DIR / "Lulu.exe"
    print(f"[SUCCESS] Build Complete! Executable created at: {exe_path}")


if __name__ == "__main__":
    build()
