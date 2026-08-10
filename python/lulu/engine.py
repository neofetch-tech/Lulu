"""
High-level model wrapper: sits between the raw C++ `lulu_core.LuluEngine`
and the CLI. Owns chat templating and conversation history so the CLI
layer stays dumb (just I/O).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import lulu_core


# Llama 3.1's instruct chat template. If you add other model families
# later (Mistral, Qwen, etc.), this is the piece that needs to grow into
# a small registry keyed by model type.
def _build_llama31_prompt(messages: list[dict[str, str]]) -> str:
    parts = ["<|begin_of_text|>"]
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>")
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
    return "".join(parts)


@dataclass
class ChatSession:
    """A stateful conversation against one loaded model."""

    model_path: str
    n_ctx: int = 4096
    n_gpu_layers: int = 0
    system_prompt: Optional[str] = None

    _engine: lulu_core.LuluEngine = field(init=False, repr=False)
    _history: list[dict[str, str]] = field(init=False, default_factory=list, repr=False)

    def __post_init__(self):
        self._engine = lulu_core.LuluEngine()
        self._engine.load(self.model_path, self.n_ctx, self.n_gpu_layers)
        if self.system_prompt:
            self._history.append({"role": "system", "content": self.system_prompt})

    @property
    def model_description(self) -> str:
        return self._engine.model_description()

    def reset(self) -> None:
        self._history = []
        if self.system_prompt:
            self._history.append({"role": "system", "content": self.system_prompt})

    def send(
        self,
        user_message: str,
        max_tokens: int = 512,
        temperature: float = 0.8,
        top_p: float = 0.95,
        on_token: Optional[Callable[[str], bool]] = None,
    ) -> str:
        """Send a user message, get the assistant's reply.

        If on_token is given, it's called once per generated token
        (streaming) and this returns the full text once generation is
        done. Return False from on_token to stop generation early.
        """
        self._history.append({"role": "user", "content": user_message})
        prompt = _build_llama31_prompt(self._history)

        params = lulu_core.GenerationParams()
        params.max_tokens = max_tokens
        params.temperature = temperature
        params.top_p = top_p

        if on_token:
            chunks: list[str] = []

            def _callback(token: str) -> bool:
                chunks.append(token)
                return on_token(token)

            self._engine.generate_stream(prompt, params, _callback)
            reply = "".join(chunks)
        else:
            reply = self._engine.generate(prompt, params)

        self._history.append({"role": "assistant", "content": reply})
        return reply

    def close(self) -> None:
        self._engine.unload()

    def __enter__(self) -> "ChatSession":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
