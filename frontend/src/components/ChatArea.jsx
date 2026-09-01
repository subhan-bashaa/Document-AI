// components/ChatArea.jsx — Phase 12 + 13 Complete Implementation
//
// Phase 12: Full chat UI with markdown-like rendering, copy button,
//           clear chat, character counter, better empty states
// Phase 13: Source cards with page badges, expandable source panel
//
// FIX: Chat input was disabled when hasDocuments=false.
//      Now it's always enabled so users can type; the send is just blocked
//      with a helpful toast if no docs are uploaded.

import { useState, useRef, useEffect } from "react";
import EmptyState  from "./EmptyState";
import LoadingDots from "./LoadingDots";

export default function ChatArea({
  messages      = [],
  isLoading     = false,
  hasDocuments  = false,
  onSendMessage = () => {},
  inputValue    = "",
  onInputChange = () => {},
  onClearChat   = () => {},
}) {
  const [copiedIndex, setCopiedIndex]   = useState(null);
  const [noDocToast,  setNoDocToast]    = useState(false);
  const [expandedSrc, setExpandedSrc]   = useState(null);
  const bottomRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Submit handler — always allow typing, warn if no docs
  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;
    if (!hasDocuments) {
      setNoDocToast(true);
      setTimeout(() => setNoDocToast(false), 3000);
      return;
    }
    onSendMessage(trimmed);
  }

  // Enter = submit, Shift+Enter = new line
  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  }

  // Copy an assistant message to clipboard
  async function handleCopy(text, index) {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch {
      // clipboard not available
    }
  }

  // Simple text renderer — preserves line breaks, highlights **bold**
  function renderText(text) {
    return text.split("\n").map((line, i, arr) => {
      // Bold text between **
      const parts = line.split(/\*\*(.*?)\*\*/g);
      return (
        <span key={i}>
          {parts.map((part, j) =>
            j % 2 === 1 ? <strong key={j}>{part}</strong> : part
          )}
          {i < arr.length - 1 && <br />}
        </span>
      );
    });
  }

  return (
    <section className="chat-area" role="main" aria-label="Chat interface">

      {/* ── Top Bar ───────────────────────────────────────────── */}
      {messages.length > 0 && (
        <div className="chat-topbar">
          <span className="chat-topbar-label">
            {messages.filter(m => m.role === "user").length} question{messages.filter(m => m.role === "user").length !== 1 ? "s" : ""} asked
          </span>
          <button
            className="clear-chat-btn"
            onClick={onClearChat}
            title="Clear conversation"
            aria-label="Clear conversation"
          >
            🗑 Clear Chat
          </button>
        </div>
      )}

      {/* ── Message List / Empty State ────────────────────────── */}
      <div
        className="chat-messages"
        id="chat-messages-container"
        aria-live="polite"
        aria-label="Conversation"
      >
        {/* Empty state — no documents uploaded */}
        {!hasDocuments && messages.length === 0 && <EmptyState />}

        {/* Empty state — docs uploaded but no messages yet */}
        {hasDocuments && messages.length === 0 && (
          <div className="empty-state animate-fade-in">
            <div className="empty-state-icon" aria-hidden="true">💬</div>
            <h2 className="empty-state-title">Documents ready!</h2>
            <p className="empty-state-text">
              Ask questions grounded in your uploaded documents.
              The assistant stays within the document context to support
              safer, more reliable answers.
            </p>
            <div className="example-questions">
              <p className="example-questions-label">💡 Try asking:</p>
              <button className="example-chip" onClick={() => onInputChange("What is the main topic of this document?")}>
                What is the main topic?
              </button>
              <button className="example-chip" onClick={() => onInputChange("Summarize the key points.")}>
                Summarize key points
              </button>
              <button className="example-chip" onClick={() => onInputChange("What are the important dates or deadlines?")}>
                Important dates
              </button>
            </div>
          </div>
        )}

        {/* Render all messages */}
        {messages.map((message, index) => (
          <div
            key={index}
            className={`chat-message ${message.role} animate-fade-in`}
            aria-label={`${message.role === "user" ? "You" : "DocuMind AI"}: ${message.content}`}
          >
            {/* Avatar */}
            <div className="message-avatar" aria-hidden="true">
              {message.role === "user" ? "👤" : "🧠"}
            </div>

            {/* Bubble + Sources + Actions */}
            <div className="message-content">
              <div className={`message-bubble ${message.isError ? "error" : ""}`}>
                {renderText(message.content)}
              </div>

              {/* ── Phase 13: Source Cards ───────────────────── */}
              {message.role === "assistant" &&
               message.sources &&
               message.sources.length > 0 && (
                <div className="sources-section" aria-label="Source references">
                  <button
                    className="sources-toggle"
                    onClick={() => setExpandedSrc(expandedSrc === index ? null : index)}
                    aria-expanded={expandedSrc === index}
                  >
                    <span>📚</span>
                    <span>{message.sources.length} Source{message.sources.length !== 1 ? "s" : ""}</span>
                    <span className="sources-chevron">{expandedSrc === index ? "▲" : "▼"}</span>
                  </button>

                  {expandedSrc === index && (
                    <div className="source-cards animate-fade-in">
                      {message.sources.map((src, i) => (
                        <div key={i} className="source-card">
                          <span className="source-card-icon">📄</span>
                          <div className="source-card-info">
                            <div className="source-card-name">{src.document}</div>
                            <div className="source-card-page">Page {src.page}</div>
                          </div>
                          <span className="source-card-badge">p.{src.page}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ── Phase 12: Copy Button ────────────────────── */}
              {message.role === "assistant" && !message.isError && (
                <div className="message-actions">
                  <button
                    className="action-btn"
                    onClick={() => handleCopy(message.content, index)}
                    title="Copy answer"
                    aria-label="Copy answer to clipboard"
                  >
                    {copiedIndex === index ? "✅ Copied!" : "📋 Copy"}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing / loading indicator */}
        {isLoading && (
          <div className="chat-message assistant animate-fade-in" role="status">
            <div className="message-avatar" aria-hidden="true">🧠</div>
            <div className="message-content">
              <div className="message-bubble">
                <LoadingDots label="Searching documents and generating answer..." />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── No-Doc Toast ───────────────────────────────────────── */}
      {noDocToast && (
        <div className="no-doc-toast animate-fade-in" role="alert">
          ⚠️ Please upload a PDF document first using the left panel.
        </div>
      )}

      {/* ── Input Area ──────────────────────────────────────────── */}
      <div className="chat-input-area">
        <form className="chat-input-wrapper" onSubmit={handleSubmit} role="search">
          <label htmlFor="question-input" className="visually-hidden">
            Ask a question about your documents
          </label>
          <textarea
            id="question-input"
            className="chat-input"
            placeholder={
              hasDocuments
                ? "Ask a question about your documents..."
                : "Type your question here — upload a PDF first to get answers"
            }
            value={inputValue}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
            aria-label="Question input"
            maxLength={2000}
          />

          <button
            type="submit"
            className="ask-button"
            id="ask-button"
            disabled={isLoading || !inputValue.trim()}
            aria-label="Send question"
          >
            {isLoading ? (
              <><span aria-hidden="true">⏳</span> Searching...</>
            ) : (
              <><span aria-hidden="true">🔍</span> Ask</>
            )}
          </button>
        </form>

        <div className="chat-input-footer">
          <p className="chat-input-hint">
            {hasDocuments
              ? "Responsible-first answers: grounded only in uploaded documents · Enter to send"
              : "⬅ Upload a PDF document to begin with source-grounded answers"
            }
          </p>
          {inputValue.length > 0 && (
            <span className="char-counter" aria-live="polite">
              {inputValue.length}/2000
            </span>
          )}
        </div>
      </div>
    </section>
  );
}
