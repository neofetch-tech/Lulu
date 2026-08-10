import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types";
import { MessageBubble } from "./MessageBubble";
import { ActivityPulse } from "./ActivityPulse";
import "./ChatView.css";

interface Props {
  loadedModelName: string | null;
  modelDescription: string | null;
  messages: ChatMessage[];
  isGenerating: boolean;
  onSend: (text: string) => void;
}

const PROMPT_PRESETS = [
  {
    title: "Write a Python script",
    desc: "High-performance async web crawler",
    prompt: "Write a complete high-performance Python script using asyncio and aiohttp for crawling URLs with a concurrency limit.",
  },
  {
    title: "Optimize C++ code",
    desc: "SIMD vectorization and memory alignment",
    prompt: "Explain how to optimize C++ loops using SIMD intrinsics and memory alignment, with code examples.",
  },
  {
    title: "Explain AI architecture",
    desc: "RoPE attention and KV caching in Llama 3.1",
    prompt: "How does Rotary Position Embedding (RoPE) work in Meta Llama 3.1, and why is KV caching crucial for local inference?",
  },
];

export function ChatView({ loadedModelName, modelDescription, messages, isGenerating, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function submit(textOverride?: string) {
    const text = (textOverride ?? draft).trim();
    if (!text || isGenerating || !loadedModelName) return;
    onSend(text);
    setDraft("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  return (
    <main className="chat">
      <header className="chat__header">
        <div className="chat__title-row">
          <div>
            <h1 className="chat__title">
              {loadedModelName ? "Llama 3.1 Instruct" : "No Model Loaded"}
              <ActivityPulse active={isGenerating} />
            </h1>
            {modelDescription && <p className="chat__subtitle">{modelDescription}</p>}
          </div>
        </div>

        {loadedModelName && (
          <span style={{ fontSize: "0.7rem", color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
            Q4_K_M GGUF
          </span>
        )}
      </header>

      <div className="chat__messages" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="chat__empty-container">
            <div className="chat__empty-logo">
              <img src="./logo.png" alt="Lulu" />
            </div>
            <h2 className="chat__empty-title">Lulu</h2>
            <p className="chat__empty-subtitle">
              {loadedModelName
                ? "Llama 3.1 is loaded and running locally on your hardware. Ask anything or pick a prompt below."
                : "Load Llama 3.1 from the sidebar to start local inference."}
            </p>

            {loadedModelName && (
              <div className="prompt-chips">
                {PROMPT_PRESETS.map((preset, idx) => (
                  <button key={idx} className="prompt-chip" onClick={() => submit(preset.prompt)}>
                    <span className="prompt-chip__title">{preset.title}</span>
                    <span className="prompt-chip__desc">{preset.desc}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}
      </div>

      <div className="chat__input-container">
        <div className="chat__input-wrapper glow-border">
          <textarea
            ref={textareaRef}
            className="chat__input"
            placeholder={
              loadedModelName
                ? "Message Llama 3.1... (Shift+Enter for new line)"
                : "Load a model from the sidebar to start chatting..."
            }
            value={draft}
            disabled={!loadedModelName}
            onChange={(e) => {
              setDraft(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
            }}
          />
          <div className="chat__input-actions">
            <span className="chat__input-hint">
              {isGenerating ? "Generating..." : "Enter to send · Shift+Enter for new line"}
            </span>
            <button
              className="btn btn--primary chat__send-btn"
              onClick={() => submit()}
              disabled={!loadedModelName || isGenerating || !draft.trim()}
            >
              {isGenerating ? "Generating..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
