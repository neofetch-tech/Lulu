# Lulu

Run large language models locally. C++ core (a thin wrapper over
[llama.cpp](https://github.com/ggerganov/llama.cpp)) + Python CLI on top.

> Name unofficial, subject to appeal and replacement.

## Architecture

```
lulu/
├── engine/                  # C++ core
│   ├── include/lulu_engine.h
│   ├── src/lulu_engine.cpp  # wraps llama.cpp's C API (load, tokenize, generate)
│   ├── src/bindings.cpp     # pybind11 -> exposes it as `lulu_core` to Python
│   └── CMakeLists.txt
├── python/lulu/              # Python package (what `pip install` ships)
│   ├── cli.py                 # `lulu run / pull / list / rm`
│   ├── engine.py               # ChatSession: chat templating + history over lulu_core
│   ├── registry.py             # model download/cache management (via HF Hub)
│   ├── desktop/                 # React desktop app's Python side
│   │   ├── app.py                # entry point (`lulu-desktop`), opens the pywebview window
│   │   └── api.py                # window.pywebview.api — the JS<->Python bridge
│   └── gui/                    # PySide6 desktop app (earlier prototype)
│       ├── app.py               # entry point (`lulu-gui`)
│       ├── main_window.py       # model picker + chat + status bar
│       ├── chat_widget.py       # message bubbles, input box
│       └── worker.py            # QThread wrappers so generation doesn't freeze the UI
├── frontend/                 # React + TypeScript + Vite (the actual UI)
│   ├── src/
│   │   ├── api.ts               # typed wrapper over window.pywebview.api + token streaming
│   │   ├── App.tsx               # app state: models, loaded session, messages
│   │   └── components/           # Sidebar, ChatView, MessageBubble, ActivityPulse
│   └── dist/                   # `npm run build` output — what lulu-desktop actually loads
├── CMakeLists.txt            # root: fetches llama.cpp + pybind11, builds everything
└── pyproject.toml            # scikit-build-core: CMake + Python in one `pip install`
```

`lulu_core` (C++) has zero opinions about chat formatting, model registries,
or CLI UX — it only knows "load a GGUF file" and "generate tokens." Everything
product-y lives in Python, which is where you'll want to iterate fastest.

## Prerequisites

- CMake >= 3.18
- A C++17 compiler
  - **Windows**: Visual Studio 2022 with the "Desktop development with C++" workload (gives you MSVC + CMake integration). Also install [Ninja](https://ninja-build.org/) (`pip install ninja`) — it builds noticeably faster than the default VS generator.
  - **Linux/macOS**: gcc/clang, whatever you already have
- Python >= 3.9
- Git (llama.cpp and pybind11 are pulled in automatically via CMake
  `FetchContent` — no manual submodule setup needed)

### Windows-specific notes

- **Long paths**: llama.cpp's source tree is deep. If the build fails with
  path-too-long errors, either enable long paths
  (`git config --system core.longpaths true` + enable `LongPathsEnabled` in
  the registry / via `gpedit`) or clone somewhere shallow like `C:\lulu`
  instead of nesting it inside `Downloads\...\...`.
- **Open a "Developer PowerShell for VS 2022"** (or run `vcvarsall.bat`)
  before `pip install -e .`, so CMake can find the MSVC compiler.
- The `-fPIC` handling in the root `CMakeLists.txt` is a GCC/Clang thing —
  CMake just ignores it on MSVC, nothing to change there.

## Build & install

```bash
git clone <this-repo> lulu && cd lulu
pip install -e .
```

The first build will take a few minutes — it's compiling llama.cpp from
source. Subsequent builds are incremental.

To also install the desktop GUI:

```bash
pip install -e ".[gui]"
```

### GPU acceleration

By default this builds CPU-only. To enable GPU offload, pass the relevant
llama.cpp build flag through at install time:

```bash
# NVIDIA (CUDA)
CMAKE_ARGS="-DGGML_CUDA=ON" pip install -e .

# Apple Silicon (Metal) — usually auto-detected, but to force it:
CMAKE_ARGS="-DGGML_METAL=ON" pip install -e .
```

Then pass `--n-gpu-layers N` to `lulu run` to offload N layers to the GPU
(`-1` or a large number offloads everything that fits).

## Usage

```bash
# Download Llama 3.1 8B Instruct (Q4_K_M, ~4.9GB)
lulu pull llama3.1

# See what's downloaded
lulu list

# Chat
lulu run llama3.1

# With options
lulu run llama3.1 --n-gpu-layers 32 --system "You are a terse assistant."

# Free up disk space
lulu rm llama3.1
```

## GUI

Two GUI options exist right now — pick one, or keep both around while you
decide which direction to invest in.

### Desktop app (React + pywebview) — recommended

A real interface: React frontend, rendered in a native window via
[pywebview](https://pywebview.flowrl.com/) (WebView2 on Windows), talking
to the same Python `ChatSession` engine underneath. No separate server —
Python functions are exposed straight to the page as `window.pywebview.api`.

```bash
# one-time: build the frontend
cd frontend
npm install
npm run build
cd ..

# install the desktop shell + run it
pip install -e ".[desktop]"
lulu-desktop
```

Re-run `npm run build` in `frontend/` any time you change the React code —
`lulu-desktop` just loads whatever's in `frontend/dist/`. For active
frontend development, `npm run dev` inside `frontend/` gives you Vite's
hot-reload in a plain browser tab (the API calls will show a clear
"not running inside the Lulu desktop shell" error there, since
`window.pywebview` only exists inside the native window — that's expected).

**Streaming**: `send_message()` in `python/lulu/desktop/api.py` returns
immediately and streams tokens back into the page via `window.evaluate_js()`
from a background thread — see that file's docstring for the full flow.

### PySide6 (Qt widgets) — earlier prototype

Still in the repo under `python/lulu/gui/`. Simpler to reason about (no
JS/build step) but visually a standard Qt app rather than a custom design.

```bash
pip install -e ".[gui]"
lulu-gui
```

## Roadmap

- [x] Phase 1 — C++ core (load/tokenize/generate) + pybind11 bindings
- [x] Phase 1 — CLI: `run`, `pull`, `list`, `rm`
- [x] Phase 1 — Desktop GUI (PySide6): model picker, streaming chat
- [x] Phase 3 — React desktop app (pywebview): custom UI, same streaming engine
- [ ] Phase 2 — KV-cache context shifting for long conversations
- [ ] Phase 2 — GUI settings panel (context size, GPU layers, temperature)
- [ ] Phase 3 — REST API server (FastAPI), Ollama-compatible endpoints
- [ ] Phase 4 — Multi-model families (chat template registry beyond Llama 3.1)
- [ ] Phase 5 — Concurrent request handling, model swapping/unloading policy
- [ ] Phase 5 — System tray icon, packaged Windows installer (PyInstaller)

## Known rough edges (day 1)

- No context-window shifting yet — long chats will hit the `n_ctx` wall and
  stop generating rather than gracefully truncating history.
- Only Llama 3.1's chat template is implemented (`engine.py`); other model
  families will produce garbage output until their template is added.
- Single model, single session at a time — no server/concurrency layer yet.
