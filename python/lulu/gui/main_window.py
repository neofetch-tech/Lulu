from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QLabel, QMessageBox, QStatusBar,
)

from lulu import registry
from lulu.engine import ChatSession
from lulu.gui.chat_widget import ChatWidget
from lulu.gui.worker import GenerationWorker, ModelLoadWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lulu")
        self.resize(900, 700)

        self._session: ChatSession | None = None
        self._current_bot_bubble = None
        self._gen_worker: GenerationWorker | None = None
        self._load_worker: ModelLoadWorker | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- top bar: model picker ------------------------------------------
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Model:"))

        self._model_combo = QComboBox()
        self._refresh_model_list()
        top_bar.addWidget(self._model_combo, stretch=1)

        self._load_button = QPushButton("Load")
        self._load_button.clicked.connect(self._on_load_clicked)
        top_bar.addWidget(self._load_button)

        root.addLayout(top_bar)

        # --- chat area -----------------------------------------------------
        self._chat = ChatWidget()
        self._chat.message_submitted.connect(self._on_message_submitted)
        self._chat.stop_requested.connect(self._on_stop_requested)
        self._chat.set_busy(True)  # nothing loaded yet
        root.addWidget(self._chat, stretch=1)

        # --- status bar ------------------------------------------------------
        self._status = QStatusBar()
        self._status.showMessage("No model loaded. Pick one above and hit Load.")
        self.setStatusBar(self._status)

    # -- model list / loading -----------------------------------------------

    def _refresh_model_list(self) -> None:
        self._model_combo.clear()
        local_models = registry.list_models()
        if not local_models:
            self._model_combo.addItem("No models downloaded — use `lulu pull` first")
            self._model_combo.setEnabled(False)
            return
        self._model_combo.setEnabled(True)
        for m in local_models:
            self._model_combo.addItem(m.name)

    def _on_load_clicked(self) -> None:
        name = self._model_combo.currentText()
        entry = registry.get(name)
        if entry is None:
            QMessageBox.warning(self, "Lulu", f"Model '{name}' not found locally.")
            return

        if self._session is not None:
            self._session.close()
            self._session = None

        self._load_button.setEnabled(False)
        self._status.showMessage(f"Loading {name}...")

        self._load_worker = ModelLoadWorker(
            model_path=entry.path, n_ctx=4096, n_gpu_layers=0, system_prompt=None,
        )
        self._load_worker.loaded.connect(self._on_model_loaded)
        self._load_worker.failed.connect(self._on_model_load_failed)
        self._load_worker.start()

    def _on_model_loaded(self, session: ChatSession) -> None:
        self._session = session
        self._load_button.setEnabled(True)
        self._chat.set_busy(False)
        self._status.showMessage(f"Loaded — {session.model_description}")

    def _on_model_load_failed(self, error: str) -> None:
        self._load_button.setEnabled(True)
        self._status.showMessage("Failed to load model.")
        QMessageBox.critical(self, "Lulu", f"Failed to load model:\n{error}")

    # -- chat -----------------------------------------------------------------

    def _on_message_submitted(self, text: str) -> None:
        if self._session is None:
            QMessageBox.information(self, "Lulu", "Load a model first.")
            return

        self._chat.add_message(text, role="user")
        self._chat.clear_input()
        self._current_bot_bubble = self._chat.add_message("", role="assistant")
        self._chat.set_busy(True)
        self._status.showMessage("Generating...")

        self._gen_worker = GenerationWorker(self._session, text)
        self._gen_worker.token_received.connect(self._on_token)
        self._gen_worker.finished_ok.connect(self._on_generation_done)
        self._gen_worker.failed.connect(self._on_generation_failed)
        self._gen_worker.start()

    def _on_token(self, token: str) -> None:
        if self._current_bot_bubble:
            self._current_bot_bubble.append_text(token)

    def _on_generation_done(self, _full_reply: str) -> None:
        self._chat.set_busy(False)
        self._status.showMessage("Ready.")

    def _on_generation_failed(self, error: str) -> None:
        self._chat.set_busy(False)
        self._status.showMessage("Generation failed.")
        QMessageBox.critical(self, "Lulu", f"Generation failed:\n{error}")

    def _on_stop_requested(self) -> None:
        if self._gen_worker:
            self._gen_worker.request_stop()

    def closeEvent(self, event) -> None:
        if self._session is not None:
            self._session.close()
        super().closeEvent(event)
