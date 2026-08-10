import type { KnownModel, LocalModel } from "./types";

interface PywebviewApi {
  list_known_models(): Promise<KnownModel[]>;
  list_local_models(): Promise<LocalModel[]>;
  pull_model(name: string): Promise<LocalModel>;
  remove_model(name: string): Promise<boolean>;
  load_model(name: string, n_ctx?: number, n_gpu_layers?: number): Promise<{ description: string }>;
  unload_model(): Promise<void>;
  send_message(text: string, max_tokens?: number, temperature?: number): Promise<{ status: string }>;
}

declare global {
  interface Window {
    pywebview?: { api: PywebviewApi };
    __luluOnToken?: (token: string) => void;
    __luluOnDone?: (fullReply: string) => void;
    __luluOnError?: (message: string) => void;
    __luluOnPullProgress?: (name: string, pct: number) => void;
  }
}

type TokenHandler = (token: string) => void;
type DoneHandler = (fullReply: string) => void;
type ErrorHandler = (message: string) => void;
type ProgressHandler = (name: string, pct: number) => void;

let tokenHandler: TokenHandler | null = null;
let doneHandler: DoneHandler | null = null;
let errorHandler: ErrorHandler | null = null;
let progressHandler: ProgressHandler | null = null;

window.__luluOnToken = (token) => tokenHandler?.(token);
window.__luluOnDone = (fullReply) => {
  doneHandler?.(fullReply);
  tokenHandler = null;
  doneHandler = null;
  errorHandler = null;
};
window.__luluOnError = (message) => {
  errorHandler?.(message);
  tokenHandler = null;
  doneHandler = null;
  errorHandler = null;
};
window.__luluOnPullProgress = (name, pct) => {
  progressHandler?.(name, pct);
};

export function onStream(handlers: { onToken: TokenHandler; onDone: DoneHandler; onError: ErrorHandler }) {
  tokenHandler = handlers.onToken;
  doneHandler = handlers.onDone;
  errorHandler = handlers.onError;
}

export function onPullProgress(handler: ProgressHandler) {
  progressHandler = handler;
}

export function waitForApi(): Promise<void> {
  if (window.pywebview?.api) return Promise.resolve();
  return new Promise((resolve) => {
    window.addEventListener("pywebviewready", () => resolve(), { once: true });
    setTimeout(resolve, 1500);
  });
}

function api(): PywebviewApi {
  if (!window.pywebview?.api) {
    throw new Error(
      "Not running inside the Lulu desktop shell — start it with `lulu-desktop`, not a plain browser."
    );
  }
  return window.pywebview.api;
}

export const luluApi = {
  listKnownModels: () => api().list_known_models(),
  listLocalModels: () => api().list_local_models(),
  pullModel: (name: string) => api().pull_model(name),
  removeModel: (name: string) => api().remove_model(name),
  loadModel: (name: string, nCtx = 4096, nGpuLayers = 0) => api().load_model(name, nCtx, nGpuLayers),
  unloadModel: () => api().unload_model(),
  sendMessage: (text: string, maxTokens = 512, temperature = 0.8) =>
    api().send_message(text, maxTokens, temperature),
};
