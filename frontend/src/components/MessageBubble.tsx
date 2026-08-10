import { useState } from "react";
import type { ChatMessage } from "../types";
import "./MessageBubble.css";

interface Props {
  message: ChatMessage;
}

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  function copyCode() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        <span>{language || "code"}</span>
        <button className="code-block-copy-btn" onClick={copyCode}>
          {copied ? "✓ Copied!" : "📋 Copy"}
        </button>
      </div>
      <pre className="code-block-content">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function FormattedContent({ text }: { text: string }) {
  // Parse code blocks vs regular text
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div>
      {parts.map((part, index) => {
        if (part.startsWith("```") && part.endsWith("```")) {
          const firstLineEnd = part.indexOf("\n");
          let language = "";
          let code = "";

          if (firstLineEnd !== -1) {
            language = part.slice(3, firstLineEnd).trim();
            code = part.slice(firstLineEnd + 1, -3);
          } else {
            code = part.slice(3, -3);
          }

          return <CodeBlock key={index} code={code} language={language} />;
        }

        // Regular text parsing (paragraphs, inline code, bold)
        const lines = part.split("\n");
        return (
          <div key={index}>
            {lines.map((line, lIdx) => {
              if (!line.trim()) return <div key={lIdx} style={{ height: "8px" }} />;

              // Check for bullet list
              if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
                const content = line.trim().slice(2);
                return (
                  <ul key={lIdx} className="markdown-ul">
                    <li className="markdown-li">{renderInline(content)}</li>
                  </ul>
                );
              }

              return (
                <p key={lIdx} className="markdown-p">
                  {renderInline(line)}
                </p>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

function renderInline(str: string) {
  // Split inline code `...`
  const codeParts = str.split(/(`[^`]+`)/g);

  return codeParts.map((cp, idx) => {
    if (cp.startsWith("`") && cp.endsWith("`")) {
      return (
        <code key={idx} className="inline-code">
          {cp.slice(1, -1)}
        </code>
      );
    }

    // Split bold **...**
    const boldParts = cp.split(/(\*\*[^*]+\*\*)/g);
    return boldParts.map((bp, bIdx) => {
      if (bp.startsWith("**") && bp.endsWith("**")) {
        return <strong key={bIdx} style={{ color: "#ffffff" }}>{bp.slice(2, -2)}</strong>;
      }
      return bp;
    });
  });
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--assistant"}`}>
      <div className="message-bubble__avatar">
        {isUser ? "U" : "🦙"}
      </div>

      <div className="message-bubble__content">
        <div className="message-bubble__role-name">
          <span>{isUser ? "You" : "Llama 3.1"}</span>
        </div>

        {message.content ? (
          <FormattedContent text={message.content} />
        ) : (
          <span style={{ color: "var(--text-faint)", fontStyle: "italic" }}>Thinking...</span>
        )}
      </div>
    </div>
  );
}
