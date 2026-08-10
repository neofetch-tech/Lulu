import { useEffect, useState } from "react";
import { luluApi, onPullProgress, onStream, waitForApi } from "./api";
import type { ChatMessage, KnownModel, LocalModel } from "./types";
import { Sidebar } from "./components/Sidebar";
import { ChatView } from "./components/ChatView";
import "./App.css";

export default function App() {
  const [ready, setReady] = useState(false);
  const [connectError, setConnectError] = useState<string | null>(null);

  const [knownModels, setKnownModels] = useState<KnownModel[]>([]);
  const [localModels, setLocalModels] = useState<LocalModel[]>([]);
  const [pullingModel, setPullingModel] = useState<string | null>(null);
  const [pullProgress, setPullProgress] = useState<number | null>(null);

  const [loadedModelName, setLoadedModelName] = useState<string | null>(null);
  const [modelDescription, setModelDescription] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    onPullProgress((_name, pct) => {
      setPullProgress(pct);
    });

    waitForApi().then(async () => {
      try {
        const [known, local] = await Promise.all([luluApi.listKnownModels(), luluApi.listLocalModels()]);
        setKnownModels(known);
        setLocalModels(local);
        setReady(true);

        // Auto-load Llama 3.1 if it's locally available!
        const llamaLocal = local.find((m) => m.name === "llama3.1");
        if (llamaLocal) {
          handleLoad("llama3.1");
        }
      } catch (err) {
        setConnectError((err as Error).message);
      }
    });
  }, []);

  async function refreshLocalModels() {
    setLocalModels(await luluApi.listLocalModels());
  }

  async function handlePull(name: string) {
    setPullingModel(name);
    setPullProgress(0);
    try {
      await luluApi.pullModel(name);
      await refreshLocalModels();
      // Auto load after download finishes!
      await handleLoad(name);
    } catch (err) {
      alert(`Download failed: ${(err as Error).message}`);
    } finally {
      setPullingModel(null);
      setPullProgress(null);
    }
  }

  async function handleLoad(name: string) {
    try {
      const { description } = await luluApi.loadModel(name);
      setLoadedModelName(name);
      setModelDescription(description);
    } catch (err) {
      alert(`Failed to load model: ${(err as Error).message}`);
    }
  }

  async function handleRemove(name: string) {
    await luluApi.removeModel(name);
    if (loadedModelName === name) {
      setLoadedModelName(null);
      setModelDescription(null);
    }
    await refreshLocalModels();
  }

  function handleNewChat() {
    setMessages([]);
  }

  function handleSend(text: string) {
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    const assistantId = crypto.randomUUID();
    const assistantMsg: ChatMessage = { id: assistantId, role: "assistant", content: "" };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsGenerating(true);

    onStream({
      onToken: (token) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + token } : m))
        );
      },
      onDone: () => setIsGenerating(false),
      onError: (message) => {
        setIsGenerating(false);
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: `⚠ ${message}` } : m))
        );
      },
    });

    luluApi.sendMessage(text).catch((err) => {
      setIsGenerating(false);
      alert(`Failed to send message: ${(err as Error).message}`);
    });
  }

  if (connectError) {
    return (
      <div className="connect-error">
        <h2>⚠️ Bridge Connection Error</h2>
        <p>{connectError}</p>
      </div>
    );
  }

  if (!ready) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: "1.1rem" }}>
          Initializing Lulu AI Engine...
        </p>
      </div>
    );
  }

  return (
    <div className="app">
      <Sidebar
        knownModels={knownModels}
        localModels={localModels}
        loadedModelName={loadedModelName}
        pullingModel={pullingModel}
        pullProgress={pullProgress}
        onPull={handlePull}
        onLoad={handleLoad}
        onRemove={handleRemove}
        onNewChat={handleNewChat}
      />
      <ChatView
        loadedModelName={loadedModelName}
        modelDescription={modelDescription}
        messages={messages}
        isGenerating={isGenerating}
        onSend={handleSend}
      />
    </div>
  );
}
