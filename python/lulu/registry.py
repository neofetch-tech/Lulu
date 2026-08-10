"""
Model registry: knows how to pull GGUF models down from the Hugging Face
Hub, where Lulu keeps them on disk, and how to list/remove them.
"""

from __future__ import annotations

import json
import shutil
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Callable

LULU_HOME = Path.home() / ".lulu"
MODELS_DIR = LULU_HOME / "models"
MANIFEST_PATH = LULU_HOME / "manifest.json"

KNOWN_MODELS: dict[str, dict[str, str]] = {
    "llama3.1": {
        "repo_id": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "description": "Meta Llama 3.1 8B Instruct, Q4_K_M quantization (~4.9GB)",
    },
    "llama3.1:70b": {
        "repo_id": "bartowski/Meta-Llama-3.1-70B-Instruct-GGUF",
        "filename": "Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf",
        "description": "Meta Llama 3.1 70B Instruct, Q4_K_M quantization (~42GB)",
    },
}


@dataclass
class ModelEntry:
    name: str
    path: str
    repo_id: str
    filename: str
    size_bytes: int

    def to_dict(self) -> dict:
        return asdict(self)


def _ensure_dirs() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_PATH.exists():
        MANIFEST_PATH.write_text(json.dumps({}))


def _load_manifest() -> dict:
    _ensure_dirs()
    return json.loads(MANIFEST_PATH.read_text())


def _save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def resolve_alias(name: str) -> tuple[str, str]:
    entry = KNOWN_MODELS[name]
    return entry["repo_id"], entry["filename"]


def pull(name: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> ModelEntry:
    from huggingface_hub import hf_hub_download

    repo_id, filename = resolve_alias(name)
    _ensure_dirs()
    target_dir = MODELS_DIR / name.replace(":", "_")
    target_dir.mkdir(parents=True, exist_ok=True)

    stop_monitor = False
    if progress_callback:
        def _monitor():
            while not stop_monitor:
                time.sleep(0.4)
                for p in target_dir.rglob("*"):
                    if p.is_file():
                        size = p.stat().st_size
                        total = 4_900_000_000 if "llama3.1" in name else 42_000_000_000
                        progress_callback(size, total)

        threading.Thread(target=_monitor, daemon=True).start()

    try:
        local_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=target_dir,
        )
    finally:
        stop_monitor = True

    entry = ModelEntry(
        name=name,
        path=str(local_path),
        repo_id=repo_id,
        filename=filename,
        size_bytes=Path(local_path).stat().st_size,
    )

    manifest = _load_manifest()
    manifest[name] = entry.to_dict()
    _save_manifest(manifest)

    return entry


def get(name: str) -> Optional[ModelEntry]:
    manifest = _load_manifest()
    data = manifest.get(name)
    return ModelEntry(**data) if data else None


def list_models() -> list[ModelEntry]:
    manifest = _load_manifest()
    return [ModelEntry(**data) for data in manifest.values()]


def remove(name: str) -> bool:
    manifest = _load_manifest()
    entry = manifest.pop(name, None)
    if entry is None:
        return False

    model_dir = MODELS_DIR / name.replace(":", "_")
    if model_dir.exists():
        shutil.rmtree(model_dir)

    _save_manifest(manifest)
    return True
