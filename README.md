# Lulu

Lulu is an open-source local AI runtime focused on running large language models directly on the user's hardware.

The project provides a desktop application and runtime layer for managing, loading, and interacting with local models without requiring a remote inference service.

Lulu currently focuses on Meta Llama 3.1 and uses `llama.cpp` as its inference backend.

## Overview

Lulu is designed around a simple principle:

> Run AI locally, keep control of the model, and avoid unnecessary cloud dependencies.

The project combines a native inference backend with a Python runtime layer and a modern desktop interface built with React, TypeScript, and Vite.

Current development is focused on Llama 3.1 support, GGUF models, local inference, model management, and runtime usability.

## Features

- Local LLM inference
- Meta Llama 3.1 support
- GGUF model support
- Native C++ backend integration
- Python integration
- React-based desktop interface
- TypeScript frontend
- Vite-based frontend tooling
- Local model management
- Model registry
- Model loading and unloading
- Model information display
- Active model selection
- Prompt presets
- Runtime status
- Open-source development

## Architecture

Lulu is composed of several layers.

+--------------------------------+
|       React + TypeScript       |
|         Desktop UI             |
+----------------+---------------+
                 |
                 v
+--------------------------------+
|             Vite               |
|       Frontend Tooling         |
+----------------+---------------+
                 |
                 v
+--------------------------------+
|        Python Runtime          |
|    CLI / Registry / Server     |
+----------------+---------------+
                 |
                 v
+--------------------------------+
|          C++ Bindings          |
|      Native Integration        |
+----------------+---------------+
                 |
                 v
+--------------------------------+
|           llama.cpp            |
|       Inference Backend        |
+----------------+---------------+
                 |
                 v
+--------------------------------+
|         GGUF Model             |
|          Llama 3.1             |
+--------------------------------+

The architecture is intentionally split between the user-facing application layer and the native inference layer.

The frontend is responsible for the user interface and application experience, while the runtime and native layers handle model management and inference.

## Current Backend

Lulu currently uses `llama.cpp` as its inference backend.

This allows the project to focus on runtime integration, model management, user experience, and local execution while relying on a mature native inference implementation.

Future versions may introduce additional native components and reduce the dependency on external inference backends where appropriate.

## Supported Models

### Currently Supported

- Meta Llama 3.1
- GGUF model format

Lulu currently prioritizes Llama 3.1 rather than attempting to support every available model architecture.

Additional architectures may be introduced as the runtime matures.

## Model Management

Lulu provides a local model management interface.

Users can:

- View available models
- Download models
- Load models into the runtime
- Unload models
- View model information
- Select the active model

Model files remain on the user's local machine.

## Local Inference

Lulu is designed for local execution.

Inference is performed on the user's own hardware through the configured backend.

This provides several advantages:

- No mandatory cloud inference
- No remote model execution
- Local model files
- Greater control over data
- Offline-capable architecture
- Hardware-dependent performance

Actual performance depends on the selected model, quantization, hardware, memory, and backend configuration.

## Technology Stack

### Core

- C++
- Python
- `llama.cpp`
- GGUF

### Frontend

- React
- TypeScript
- Vite

### Build and Development

- CMake
- Python packaging
- Native C++ bindings

The frontend and inference layers are intentionally separated so that the runtime can evolve independently from the user interface.

## Project Structure

```text
Lulu/
├── engine/
│   ├── src/
│   └── include/
│
├── lulu/
│   ├── cli.py
│   ├── registry.py
│   └── server.py
│
├── frontend/
│   ├── src/
│   └── ...
│
├── pyproject.toml
└── README.md
```

The project structure is currently evolving and may change between releases.

## Requirements

- Windows, Linux, or another supported platform
- Python 3.x
- C++ compiler
- CMake
- Node.js and npm
- Sufficient system memory for the selected model
- A compatible GGUF model

Hardware requirements depend heavily on the selected model and quantization.

## Installation

Installation instructions will be provided as the project moves toward its first public release.

For development builds, clone the repository:

```bash
git clone https://github.com/USERNAME/lulu.git
cd lulu
```

Install the Python package:

```bash
pip install -e .
```

Install frontend dependencies:

```bash
npm install
```

Build instructions may change during early development.

## Usage

Once Lulu is installed and a compatible model is available, the application can be started through the desktop interface or command-line interface.

The exact commands and configuration options are still under development.

## Roadmap

### Runtime

- [x] Local model loading
- [x] Llama 3.1 support
- [x] GGUF support
- [x] C++ backend integration
- [x] Python integration
- [x] Model registry
- [ ] Improved context management
- [ ] Advanced KV cache management
- [ ] Improved memory management
- [ ] Runtime profiling
- [ ] Performance optimizations

### Desktop

- [x] React interface
- [x] TypeScript frontend
- [x] Vite integration
- [x] Model management interface
- [x] Model status
- [x] Chat interface
- [x] Prompt presets
- [ ] Advanced runtime settings
- [ ] Hardware monitoring
- [ ] Improved model management
- [ ] Custom model configuration

### Model Support

- [x] Llama 3.1
- [ ] Gemma
- [ ] Additional Llama versions
- [ ] Additional model architectures

### Backend

- [x] `llama.cpp` integration
- [ ] Native Lulu inference components
- [ ] CPU optimizations
- [ ] SIMD optimizations
- [ ] Additional hardware backends
- [ ] GPU acceleration improvements

## Project Status

Lulu is currently in active development.

The project should be considered experimental software. APIs, interfaces, architecture, and supported models may change without backwards compatibility during early development.

The current goal is to establish a stable local runtime foundation before expanding model and hardware support.

## Contributing

Contributions are welcome.

Lulu is an open-source project and development is currently focused on improving local inference, runtime architecture, model management, and the desktop experience.

Before submitting a large change, consider opening an issue to discuss the proposed implementation.

Pull requests should:

1. Follow the existing project structure.
2. Keep changes focused.
3. Include appropriate testing where possible.
4. Document user-facing changes.
5. Avoid introducing unnecessary dependencies.

## License

Lulu is open-source software.

The project license will be specified before the first stable release.

Dependencies used by Lulu may be distributed under their respective licenses.

## Acknowledgements

Lulu currently relies on the following major open-source technologies:

- `llama.cpp` for local model inference
- GGUF for model storage and distribution
- React for the user interface
- TypeScript for frontend development
- Vite for frontend tooling

Lulu would not be possible without the work of the open-source projects and communities behind these technologies.

## Disclaimer

Lulu is an experimental project and is not currently intended for production-critical workloads.

Model performance, memory usage, compatibility, and hardware requirements vary depending on the selected model and system configuration.
