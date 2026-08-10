"""
The bridge exposed to the frontend as `window.pywebview.api.*`.
"""

from __future__ import annotations

import json
import threading
from typing import Optional

from lulu import registry
from lulu.engine import ChatSession


class LuluAPI:
    def __init__(self):
        self._session: Optional[ChatSession] = None
        self._window = None

    def set_window(self, window) -> None:
        self._window = window

    # -- model registry -----------------------------------------------------

    def list_known_models(self) -> list[dict]:
        return [{"name": name, **info} for name, info in registry.KNOWN_MODELS.items()]

    def list_local_models(self) -> list[dict]:
        return [m.to_dict() for m in registry.list_models()]

    def pull_model(self, name: str) -> dict:
        def on_progress(done_bytes: int, total_bytes: int):
            if self._window and total_bytes > 0:
                pct = min(100, int((done_bytes / total_bytes) * 100))
                self._window.evaluate_js(f"window.__luluOnPullProgress?.({json.dumps(name)}, {pct})")

        entry = registry.pull(name, progress_callback=on_progress)
        return entry.to_dict()

    def remove_model(self, name: str) -> bool:
        return registry.remove(name)

    # -- chat session --------------------------------------------------------

    def load_model(self, name: str, n_ctx: int = 4096, n_gpu_layers: int = 0) -> dict:
        entry = registry.get(name)
        if entry is None:
            raise Exception(f"Model '{name}' not found locally. Pull it first.")

        if self._session is not None:
            self._session.close()

        self._session = ChatSession(model_path=entry.path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers)
        return {"description": self._session.model_description}

    def unload_model(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

    def open_url(self, url: str) -> None:
        """Open a URL in the system's default web browser (not inside the webview)."""
        import webbrowser
        webbrowser.open(url)

    def send_message(self, text: str, max_tokens: int = 512, temperature: float = 0.8) -> dict:
        if self._session is None:
            raise Exception("No model loaded.")
        if self._window is None:
            raise Exception("Window not ready yet.")

        def _run():
            try:
                def on_token(token: str) -> bool:
                    self._window.evaluate_js(f"window.__luluOnToken({json.dumps(token)})")
                    return True

                reply = self._session.send(
                    text, max_tokens=max_tokens, temperature=temperature, on_token=on_token
                )
                self._window.evaluate_js(f"window.__luluOnDone({json.dumps(reply)})")
            except Exception as exc:  # noqa: BLE001
                self._window.evaluate_js(f"window.__luluOnError({json.dumps(str(exc))})")

        threading.Thread(target=_run, daemon=True).start()
        return {"status": "started"}
