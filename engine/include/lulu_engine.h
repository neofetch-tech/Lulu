#pragma once

#include <string>
#include <functional>
#include <vector>
#include <memory>

// Forward declarations so this header doesn't force every consumer
// to pull in the full llama.cpp headers.
struct llama_model;
struct llama_context;
struct llama_sampler;

namespace lulu {

// Generation parameters exposed to Python. Keep this a plain struct
// so it's trivial to bind with pybind11's automatic conversion.
struct GenerationParams {
    int32_t max_tokens   = 512;
    float   temperature  = 0.8f;
    float   top_p        = 0.95f;
    int32_t top_k        = 40;
    float   repeat_penalty = 1.1f;
    uint32_t seed         = 0xFFFFFFFF; // 0xFFFFFFFF == llama.cpp's LLAMA_DEFAULT_SEED (random)
};

// Called once per generated token. Returning false stops generation early
// (this is how we support Ctrl-C / "stop" from the Python side).
using TokenCallback = std::function<bool(const std::string& token_text)>;

// Thin, RAII-friendly wrapper around a loaded llama.cpp model + context.
// One LuluEngine == one model resident in memory. The Python layer owns
// the lifetime (create it, use it, let it go out of scope to free VRAM/RAM).
class LuluEngine {
public:
    LuluEngine();
    ~LuluEngine();

    LuluEngine(const LuluEngine&) = delete;
    LuluEngine& operator=(const LuluEngine&) = delete;

    // Loads a GGUF model from disk. Throws std::runtime_error on failure
    // (pybind11 turns that into a Python RuntimeError automatically).
    void load(const std::string& model_path, int32_t n_ctx, int32_t n_gpu_layers);

    void unload();
    bool is_loaded() const { return model_ != nullptr; }

    // Blocking, non-streaming convenience method: returns the full
    // completion as one string.
    std::string generate(const std::string& prompt, const GenerationParams& params);

    // Streaming variant: invokes `callback` once per token as it's produced.
    void generate_stream(const std::string& prompt,
                          const GenerationParams& params,
                          TokenCallback callback);

    std::vector<int32_t> tokenize(const std::string& text, bool add_special) const;
    std::string detokenize(const std::vector<int32_t>& tokens) const;

    int32_t n_ctx() const;
    std::string model_description() const;

private:
    llama_model*   model_   = nullptr;
    llama_context* context_ = nullptr;

    // Internal helper shared by generate()/generate_stream().
    void run_generation(const std::string& prompt,
                         const GenerationParams& params,
                         const TokenCallback& callback);
};

} // namespace lulu
