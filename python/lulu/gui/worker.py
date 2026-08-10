"""
Runs model generation on a background QThread so the UI stays responsive
while tokens are streaming in. ChatSession.send() is blocking (it loops
until generation finishes), so it must never run on the GUI thread.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from lulu.engine import ChatSession


class GenerationWorker(QThread):
    """One instance = one in-flight generation request."""

    token_received = Signal(str)
    finished_ok = Signal(str)      # full reply text
    failed = Signal(str)           # error message

    def __init__(self, session: ChatSession, user_message: str,
                 max_tokens: int = 512, temperature: float = 0.8, parent=None):
        super().__init__(parent)
        self._session = session
        self._user_message = user_message
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        try:
            def _on_token(token: str) -> bool:
                self.token_received.emit(token)
                return not self._stop_requested

            reply = self._session.send(
                self._user_message,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                on_token=_on_token,
            )
            self.finished_ok.emit(reply)
        except Exception as exc:  # noqa: BLE001 — surface any engine error to the UI
            self.failed.emit(str(exc))


class ModelLoadWorker(QThread):
    """Loading an 8B model can take several seconds — don't freeze the UI."""

    loaded = Signal(object)   # emits the constructed ChatSession
    failed = Signal(str)

    def __init__(self, model_path: str, n_ctx: int, n_gpu_layers: int,
                 system_prompt: str | None, parent=None):
        super().__init__(parent)
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._system_prompt = system_prompt

    def run(self) -> None:
        try:
            session = ChatSession(
                model_path=self._model_path,
                n_ctx=self._n_ctx,
                n_gpu_layers=self._n_gpu_layers,
                system_prompt=self._system_prompt,
            )
            self.loaded.emit(session)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
