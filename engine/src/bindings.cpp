#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

#include "lulu_engine.h"

namespace py = pybind11;
using namespace lulu;

PYBIND11_MODULE(lulu_core, m) {
    m.doc() = "Lulu C++ inference core (pybind11 bindings over llama.cpp)";

    py::class_<GenerationParams>(m, "GenerationParams")
        .def(py::init<>())
        .def_readwrite("max_tokens", &GenerationParams::max_tokens)
        .def_readwrite("temperature", &GenerationParams::temperature)
        .def_readwrite("top_p", &GenerationParams::top_p)
        .def_readwrite("top_k", &GenerationParams::top_k)
        .def_readwrite("repeat_penalty", &GenerationParams::repeat_penalty)
        .def_readwrite("seed", &GenerationParams::seed)
        .def("__repr__", [](const GenerationParams& p) {
            return "<GenerationParams max_tokens=" + std::to_string(p.max_tokens) +
                   " temperature=" + std::to_string(p.temperature) +
                   " top_p=" + std::to_string(p.top_p) + ">";
        });

    py::class_<LuluEngine>(m, "LuluEngine")
        .def(py::init<>())
        .def("load", &LuluEngine::load,
             py::arg("model_path"), py::arg("n_ctx") = 4096, py::arg("n_gpu_layers") = 0,
             // loading can take a while — don't hold the GIL hostage
             py::call_guard<py::gil_scoped_release>())
        .def("unload", &LuluEngine::unload)
        .def("is_loaded", &LuluEngine::is_loaded)
        .def("n_ctx", &LuluEngine::n_ctx)
        .def("model_description", &LuluEngine::model_description)
        .def("tokenize", &LuluEngine::tokenize,
             py::arg("text"), py::arg("add_special") = true)
        .def("detokenize", &LuluEngine::detokenize, py::arg("tokens"))
        .def("generate", &LuluEngine::generate,
             py::arg("prompt"), py::arg("params") = GenerationParams(),
             py::call_guard<py::gil_scoped_release>(),
             "Blocking call — returns the full completion as one string.")
        .def("generate_stream",
             [](LuluEngine& self, const std::string& prompt, const GenerationParams& params,
                py::function py_callback) {
                 // Bridge: llama.cpp calls us from C++ per-token; we hop
                 // back into Python (re-acquiring the GIL) to hand the
                 // token to the caller's Python callback.
                 self.generate_stream(prompt, params, [&py_callback](const std::string& token) -> bool {
                     py::gil_scoped_acquire acquire;
                     py::object result = py_callback(token);
                     return result.is_none() ? true : result.cast<bool>();
                 });
             },
             py::arg("prompt"), py::arg("params"), py::arg("callback"),
             py::call_guard<py::gil_scoped_release>(),
             "Streaming call — invokes callback(token_str) -> bool|None per token. "
             "Return False from the callback to stop generation early.");
}
