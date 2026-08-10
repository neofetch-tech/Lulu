import { useState } from "react";
import type { KnownModel, LocalModel } from "../types";
import "./Sidebar.css";

interface Props {
  knownModels: KnownModel[];
  localModels: LocalModel[];
  loadedModelName: string | null;
  pullingModel: string | null;
  pullProgress?: number | null;
  onPull: (name: string) => void;
  onLoad: (name: string) => void;
  onRemove: (name: string) => void;
  onNewChat?: () => void;
}

function formatSize(bytes: number): string {
  const gb = bytes / 1024 ** 3;
  return `${gb.toFixed(1)} GB`;
}

// Meta logo — loaded from public/Meta_(9).svg with relative path for pywebview
function MetaLogo() {
  return <img src="./Meta_(9).svg" alt="Meta" className="meta-logo" style={{ width: 20, height: 20, flexShrink: 0 }} />;
}

// GitHub logo as inline SVG
function GitHubLogo() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  );
}

export function Sidebar({
  knownModels,
  localModels,
  loadedModelName,
  pullingModel,
  pullProgress,
  onPull,
  onLoad,
  onRemove,
  onNewChat,
}: Props) {
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null);
  const localNames = new Set(localModels.map((m) => m.name));

  const primaryModel = knownModels.find((m) => m.name === "llama3.1") || knownModels[0] || {
    name: "llama3.1",
    description: "Meta Llama 3.1 8B Instruct, Q4_K_M quantization (~4.9GB)",
  };

  const isPrimaryLocal = localNames.has(primaryModel.name); // used below
  const isPrimaryLoaded = loadedModelName === primaryModel.name;
  const isPrimaryPulling = pullingModel === primaryModel.name;
  const primaryLocalObj = localModels.find((m) => m.name === primaryModel.name);

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar__brand">
        <div className="sidebar__logo-wrapper">
          <img src="./logo.png" alt="Lulu" className="sidebar__logo" />
        </div>
        <div className="sidebar__brand-text">
          <span className="sidebar__wordmark">Lulu</span>
          <span className="sidebar__tagline">Local AI Runtime</span>
        </div>
      </div>

      {/* New Chat */}
      <div className="sidebar__section">
        <button
          className="btn btn--primary"
          style={{ width: "100%" }}
          onClick={onNewChat}
        >
          + New Chat
        </button>
      </div>

      {/* Section label */}
      <div className="sidebar__section-header">
        <span className="sidebar__section-label">AI Model</span>
      </div>

      <div className="sidebar__list">
        {/* Primary: Llama 3.1 card */}
        <div className={`model-hero-card ${isPrimaryLoaded ? "model-hero-card--loaded" : ""}`}>
          {isPrimaryLoaded && <span className="model-hero-card__badge">ACTIVE</span>}

          <div className="model-hero-card__title">
            <MetaLogo />
            Meta Llama 3.1
          </div>

          <p className="model-hero-card__desc">8B Instruct • Q4_K_M GGUF</p>

          <div className="model-hero-card__meta">
            <span>llama.cpp</span>
            {primaryLocalObj && <span>{formatSize(primaryLocalObj.size_bytes)}</span>}
          </div>

          {isPrimaryPulling ? (
            <div className="download-progress">
              <div className="download-progress__text">
                <span>Downloading...</span>
                <span>{pullProgress != null ? `${pullProgress}%` : "..."}</span>
              </div>
              <div className="download-progress__bar-bg">
                <div className="download-progress__bar-fill" style={{ width: `${pullProgress ?? 40}%` }} />
              </div>
            </div>
          ) : !isPrimaryLocal ? (
            <button className="btn btn--primary" style={{ width: "100%" }} onClick={() => onPull(primaryModel.name)}>
              Download Llama 3.1
            </button>
          ) : (
            <div style={{ display: "flex", gap: "7px" }}>
              <button
                className={`btn ${isPrimaryLoaded ? "btn--ghost" : "btn--primary"}`}
                style={{ flex: 1 }}
                onClick={() => onLoad(primaryModel.name)}
                disabled={isPrimaryLoaded}
              >
                {isPrimaryLoaded ? "✓ Loaded" : "Load Model"}
              </button>
              {confirmRemove === primaryModel.name ? (
                <button className="btn btn--danger" onClick={() => { onRemove(primaryModel.name); setConfirmRemove(null); }}>
                  Confirm
                </button>
              ) : (
                <button className="btn btn--ghost btn--icon" title="Remove from disk" onClick={() => setConfirmRemove(primaryModel.name)}>
                  ✕
                </button>
              )}
            </div>
          )}
        </div>

        {/* Other models */}
        {knownModels.filter((m) => m.name !== primaryModel.name).length > 0 && (
          <>
            <div className="sidebar__section-label" style={{ marginTop: "8px", padding: "0 2px" }}>Other Models</div>
            {knownModels.filter((m) => m.name !== primaryModel.name).map((model) => {
              const local = localModels.find((m) => m.name === model.name);
              const isLoaded = loadedModelName === model.name;
              const isPulling = pullingModel === model.name;
              return (
                <div key={model.name} className={`model-hero-card ${isLoaded ? "model-hero-card--loaded" : ""}`} style={{ padding: "12px" }}>
                  <div className="model-hero-card__title" style={{ fontSize: "0.88rem" }}>{model.name}</div>
                  <p className="model-hero-card__desc">{model.description}</p>
                  <button
                    className="btn btn--ghost"
                    style={{ width: "100%", marginTop: "6px" }}
                    onClick={() => local ? onLoad(model.name) : onPull(model.name)}
                    disabled={isPulling || isLoaded}
                  >
                    {isLoaded ? "✓ Loaded" : isPulling ? "Downloading..." : local ? "Load" : "Download"}
                  </button>
                </div>
              );
            })}
          </>
        )}
      </div>

      {/* Footer */}
      <div className="sidebar__footer">
        {/* GitHub link */}
        <a
          href="https://github.com/neofetch-tech/Lulu"
          className="sidebar__github-link"
          onClick={(e) => {
            e.preventDefault();
            // In pywebview open via the system browser; fall back to window.open in dev
            const url = "https://github.com/neofetch-tech/Lulu";
            if (window.pywebview?.api && typeof (window.pywebview.api as any).open_url === "function") {
              (window.pywebview.api as any).open_url(url);
            } else {
              window.open(url, "_blank");
            }
          }}
          title="View on GitHub"
        >
          <GitHubLogo />
          View on GitHub
        </a>

        <div className="sidebar__footer-info">
          <span>Status</span>
          <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <span className={`status-dot ${loadedModelName ? "status-dot--active" : ""}`} />
            {loadedModelName ? "Ready" : "Idle"}
          </span>
        </div>
        <div className="sidebar__footer-info">
          <span>Backend</span>
          <span>llama.cpp</span>
        </div>
      </div>
    </aside>
  );
}
