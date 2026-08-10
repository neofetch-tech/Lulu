"""
Desktop entry point (`lulu-desktop`). Opens a native window (WebView2 on
Windows, WebKit on macOS/Linux) showing the built React frontend, with
LuluAPI wired in as window.pywebview.api.
"""

from __future__ import annotations

import sys
from pathlib import Path

import webview

from lulu.desktop.api import LuluAPI

# Resolve FRONTEND_INDEX for both development and PyInstaller bundled mode (sys._MEIPASS)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
    FRONTEND_INDEX = BASE_DIR / "frontend" / "dist" / "index.html"
else:
    BASE_DIR = Path(__file__).resolve().parents[3]
    FRONTEND_INDEX = BASE_DIR / "frontend" / "dist" / "index.html"


def main() -> None:
    if not FRONTEND_INDEX.exists():
        raise SystemExit(
            f"Frontend build not found at {FRONTEND_INDEX}\n"
            "Run `npm install && npm run build` inside the frontend/ folder first."
        )

    # Use clean file path / URI for pywebview window
    url = FRONTEND_INDEX.as_uri()

    api = LuluAPI()
    window = webview.create_window(
        "Lulu",
        url,
        js_api=api,
        width=1200,
        height=820,
        min_size=(800, 560),
        background_color="#06090c",
    )
    api.set_window(window)
    # Enable http_server=True for reliable local asset loading across WebView2
    webview.start(http_server=True)


if __name__ == "__main__":
    main()
