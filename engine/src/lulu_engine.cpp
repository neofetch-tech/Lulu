#include "lulu_engine.h"

#include "llama.h"

#include <stdexcept>
#include <cstring>
#include <sstream>

namespace lulu {

namespace {

// llama.cpp logs straight to stderr by default; this keeps Lulu's own
// stdout clean for whatever the CLI wants to print. Flip this off (or
// route it through spdlog/etc.) once you want real logging control.
void quiet_log_callback(ggml_log_level level, const char* text, void* /*user_data*/) {
    if (level >= GGML_LOG_LEVEL_ERROR) {
        fputs(text, stderr);
    }
}

} // namespace

LuluEngine::LuluEngine() {
    static bool backend_initialized = false;
    if (!backend_initialized) {
        llama_log_set(quiet_log_callback, nullptr);
        llama_backend_init();
        backend_initialized = true;
    }
}

LuluEngine::~LuluEngine() {
    unload();
}

void LuluEngine::load(const std::string& model_path, int32_t n_ctx, int32_t n_gpu_layers) {
    unload();

    llama_model_params model_params = llama_model_default_params();
    model_params.n_gpu_layers = n_gpu_layers;

    model_ = llama_model_load_from_file(model_path.c_str(), model_params);
    if (!model_) {
        throw std::runtime_error("Lulu: failed to load model from '" + model_path + "'");
    }

    llama_context_params ctx_params = llama_context_default_params();
    ctx_params.n_ctx   = n_ctx > 0 ? n_ctx : 4096;
    ctx_params.n_batch = 512;

    context_ = llama_init_from_model(model_, ctx_params);
    if (!context_) {
        llama_model_free(model_);
        model_ = nullptr;
        throw std::runtime_error("Lulu: failed to create context for model '" + model_path + "'");
    }
}

void LuluEngine::unload() {
    if (context_) {
        llama_free(context_);
        context_ = nullptr;
    }
    if (model_) {
        llama_model_free(model_);
        model_ = nullptr;
    }
}

int32_t LuluEngine::n_ctx() const {
    return context_ ? static_cast<int32_t>(llama_n_ctx(context_)) : 0;
}

std::string LuluEngine::model_description() const {
    if (!model_) return "<no model loaded>";
    char buf[256];
    llama_model_desc(model_, buf, sizeof(buf));
    return std::string(buf);
}

std::vector<int32_t> LuluEngine::tokenize(const std::string& text, bool add_special) const {
    if (!model_) throw std::runtime_error("Lulu: tokenize() called with no model loaded");

    const llama_vocab* vocab = llama_model_get_vocab(model_);

    int32_t n_tokens = -llama_tokenize(vocab, text.c_str(), (int32_t)text.size(),
                                        nullptr, 0, add_special, true);
    std::vector<int32_t> tokens(n_tokens);
    llama_tokenize(vocab, text.c_str(), (int32_t)text.size(),
                    tokens.data(), n_tokens, add_special, true);
    return tokens;
}

std::string LuluEngine::detokenize(const std::vector<int32_t>& tokens) const {
    if (!model_) throw std::runtime_error("Lulu: detokenize() called with no model loaded");

    const llama_vocab* vocab = llama_model_get_vocab(model_);
    std::string out;
    char piece[256];
    for (int32_t tok : tokens) {
        int32_t n = llama_token_to_piece(vocab, tok, piece, sizeof(piece), 0, true);
        if (n > 0) out.append(piece, n);
    }
    return out;
}

void LuluEngine::run_generation(const std::string& prompt,
                                 const GenerationParams& params,
                                 const TokenCallback& callback) {
    if (!model_ || !context_) {
        throw std::runtime_error("Lulu: generate() called with no model loaded — call load() first");
    }

    const llama_vocab* vocab = llama_model_get_vocab(model_);

    // --- Tokenize prompt and prime the context -----------------------------
    std::vector<int32_t> prompt_tokens = tokenize(prompt, /*add_special=*/true);

    llama_batch batch = llama_batch_get_one(prompt_tokens.data(),
                                             (int32_t)prompt_tokens.size());
    if (llama_decode(context_, batch) != 0) {
        throw std::runtime_error("Lulu: llama_decode failed on prompt");
    }

    // --- Build the sampler chain --------------------------------------------
    // top-k -> top-p -> temperature -> repeat-penalty -> pick.
    // This mirrors llama.cpp's own `simple`/`main` examples; swap it out
    // for something fancier (mirostat, min-p, grammar) later.
    llama_sampler_chain_params sampler_params = llama_sampler_chain_default_params();
    llama_sampler* sampler = llama_sampler_chain_init(sampler_params);

    llama_sampler_chain_add(sampler, llama_sampler_init_top_k(params.top_k));
    llama_sampler_chain_add(sampler, llama_sampler_init_top_p(params.top_p, 1));
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(params.temperature));
    llama_sampler_chain_add(sampler, llama_sampler_init_penalties(
        llama_vocab_n_tokens(vocab), // n_vocab
        64,                          // last_n tokens considered
        params.repeat_penalty,       // repeat penalty
        0.0f,                        // frequency penalty
        0.0f                         // presence penalty
    ));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(params.seed));

    struct SamplerGuard {
        llama_sampler* s;
        ~SamplerGuard() { llama_sampler_free(s); }
    } sampler_guard{sampler};

    // --- Decode loop ---------------------------------------------------------
    int32_t n_cur = (int32_t)prompt_tokens.size();
    const int32_t n_ctx_size = n_ctx();

    for (int32_t i = 0; i < params.max_tokens; ++i) {
        llama_token new_token = llama_sampler_sample(sampler, context_, -1);

        if (llama_vocab_is_eog(vocab, new_token)) {
            break;
        }

        char piece[256];
        int32_t n = llama_token_to_piece(vocab, new_token, piece, sizeof(piece), 0, true);
        std::string token_text(piece, n > 0 ? n : 0);

        if (callback && !callback(token_text)) {
            break; // caller asked us to stop early
        }

        llama_sampler_accept(sampler, new_token);

        if (n_cur >= n_ctx_size) {
            // Out of context space — in a fuller implementation you'd
            // shift the KV cache here. For now, stop cleanly.
            break;
        }

        llama_batch next_batch = llama_batch_get_one(&new_token, 1);
        if (llama_decode(context_, next_batch) != 0) {
            throw std::runtime_error("Lulu: llama_decode failed during generation");
        }
        n_cur++;
    }
}

std::string LuluEngine::generate(const std::string& prompt, const GenerationParams& params) {
    std::string result;
    run_generation(prompt, params, [&result](const std::string& tok) {
        result += tok;
        return true;
    });
    return result;
}

void LuluEngine::generate_stream(const std::string& prompt,
                                  const GenerationParams& params,
                                  TokenCallback callback) {
    run_generation(prompt, params, callback);
}

} // namespace lulu
