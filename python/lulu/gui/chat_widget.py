"""
The chat area: a scrollable list of message bubbles plus an input box.
Kept dumb on purpose — it doesn't know about ChatSession or workers,
it just renders messages and emits a signal when the user submits one.
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QTextEdit, QPushButton, QSizePolicy, QFrame,
)


class MessageBubble(QFrame):
    def __init__(self, text: str, role: str, parent=None):
        super().__init__(parent)
        self.setObjectName("bubble")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.label)

        is_user = role == "user"
        self.setStyleSheet(f"""
            #bubble {{
                background: {"#2b5797" if is_user else "#3a3a3a"};
                border-radius: 10px;
                color: white;
            }}
        """)
        self.setMaximumWidth(560)

    def append_text(self, chunk: str) -> None:
        self.label.setText(self.label.text() + chunk)


class ChatWidget(QWidget):
    message_submitted = Signal(str)
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)

        # --- scrollable message list -----------------------------------
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._message_container = QWidget()
        self._message_layout = QVBoxLayout(self._message_container)
        self._message_layout.addStretch(1)
        self._scroll.setWidget(self._message_container)
        root.addWidget(self._scroll, stretch=1)

        # --- input row ----------------------------------------------------
        input_row = QHBoxLayout()

        self._input = QTextEdit()
        self._input.setFixedHeight(64)
        self._input.setPlaceholderText("Message Lulu... (Enter to send, Shift+Enter for newline)")
        self._input.installEventFilter(self)
        input_row.addWidget(self._input, stretch=1)

        self._send_button = QPushButton("Send")
        self._send_button.clicked.connect(self._submit)
        input_row.addWidget(self._send_button)

        self._stop_button = QPushButton("Stop")
        self._stop_button.setEnabled(False)
        self._stop_button.clicked.connect(self.stop_requested.emit)
        input_row.addWidget(self._stop_button)

        root.addLayout(input_row)

    # -- public API used by MainWindow ------------------------------------

    def add_message(self, text: str, role: str) -> MessageBubble:
        bubble = MessageBubble(text, role)
        wrapper = QHBoxLayout()
        if role == "user":
            wrapper.addStretch(1)
            wrapper.addWidget(bubble)
        else:
            wrapper.addWidget(bubble)
            wrapper.addStretch(1)

        container = QWidget()
        container.setLayout(wrapper)
        # insert before the trailing stretch
        self._message_layout.insertWidget(self._message_layout.count() - 1, container)
        self._scroll_to_bottom()
        return bubble

    def set_busy(self, busy: bool) -> None:
        self._send_button.setEnabled(not busy)
        self._stop_button.setEnabled(busy)
        self._input.setEnabled(not busy)

    def clear_input(self) -> None:
        self._input.clear()

    # -- internals -----------------------------------------------------------

    def _submit(self) -> None:
        text = self._input.toPlainText().strip()
        if not text:
            return
        self.message_submitted.emit(text)

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent
        if obj is self._input and event.type() == QEvent.KeyPress:
            key_event: QKeyEvent = event
            if key_event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (key_event.modifiers() & Qt.ShiftModifier):
                self._submit()
                return True
        return super().eventFilter(obj, event)
