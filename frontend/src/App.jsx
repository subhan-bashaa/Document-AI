// App.jsx — DocuMind AI Root Component (Phase 4)
//
// Phase 4 adds:
//   - handleUpload(file): sends the PDF to the backend, updates sidebar list
//   - uploadError state: shows server errors inside the Sidebar upload zone
//   - isUploading state: disables the upload zone while in progress
//   - onUpload prop passed to Sidebar
//   - getDocuments() called on mount to restore persisted documents

import { useState, useEffect, useRef } from "react";
import { checkHealth, uploadDocument, deleteDocument, askQuestion, summarizeDocument } from "./services/api";

import Header   from "./components/Header";
import Sidebar  from "./components/Sidebar";
import ChatArea from "./components/ChatArea";

import "./App.css";
import "./components/components.css";

export default function App() {

  // ── Backend connection status ────────────────────────────────────────────
  const [backendStatus, setBackendStatus] = useState("checking");

  // ── Document state ────────────────────────────────────────────────────────
  // Each document object: { name, size_mb, status, pages?, chunks? }
  const [documents,      setDocuments]      = useState([]);
  const [activeDocument, setActiveDocument] = useState(null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // ── Upload state ──────────────────────────────────────────────────────────
  // isUploading: true while the file is being POSTed to the backend
  // uploadError: holds any error message from the server (shown in Sidebar)
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError,  setUploadError] = useState(null);

  // ── Chat state ────────────────────────────────────────────────────────────
  const [messages,   setMessages]   = useState([]);
  const [isLoading,  setIsLoading]  = useState(false);
  const [inputValue, setInputValue] = useState("");

  // Ref to auto-scroll chat to bottom after each new message
  const messagesEndRef = useRef(null);

  // ── Health check on mount ───────────────────────────────────────────────
  useEffect(() => {
    async function init() {
      try {
        await checkHealth();
        setBackendStatus("connected");
      } catch {
        setBackendStatus("disconnected");
      }
    }

    init();
  }, []);

  // ── Auto-scroll chat to bottom ────────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 768px)");

    const handleMediaChange = (event) => {
      if (!event.matches) {
        setMobileSidebarOpen(false);
      }
    };

    handleMediaChange(mediaQuery);
    mediaQuery.addEventListener("change", handleMediaChange);

    return () => mediaQuery.removeEventListener("change", handleMediaChange);
  }, []);

  // ── Handle PDF Upload ─────────────────────────────────────────────────────
  // Called by Sidebar when the user selects or drops a PDF.
  // The file has already passed client-side checks in Sidebar.
  async function handleUpload(file) {
    setUploadError(null);    // Clear any previous upload error
    setIsUploading(true);    // Disable the upload zone

    // Add a temporary "loading" entry to the sidebar list immediately
    // so the user sees something happening right away.
    const tempDoc = {
      name:    file.name,
      size_mb: parseFloat((file.size / (1024 * 1024)).toFixed(2)),
      status:  "loading",   // Yellow dot in the sidebar
    };
    setDocuments((prev) => {
      // If a doc with the same name already exists, replace it (re-upload)
      const filtered = prev.filter((d) => d.name !== file.name);
      return [...filtered, tempDoc];
    });

    try {
      // POST the file to the Flask backend
      const response = await uploadDocument(file);

      // Replace the "loading" entry with the real document data from the server
      const uploadedDoc = {
        ...response.document,   // contains: name, size_mb, path, status
        status: "ready",        // Override to "ready" — upload succeeded
      };

      setDocuments((prev) =>
        prev.map((d) => (d.name === file.name ? uploadedDoc : d))
      );

      // Auto-select the newly uploaded document
      setActiveDocument(uploadedDoc.name);

      console.log(`[INFO] Uploaded: ${uploadedDoc.name} (${uploadedDoc.size_mb} MB)`);

    } catch (error) {
      // Remove the loading entry and show the error in the upload zone
      setDocuments((prev) => prev.filter((d) => d.name !== file.name));
      setUploadError(error.message || "Upload failed. Please try again.");
      console.error("[ERROR] Upload failed:", error.message);

    } finally {
      setIsUploading(false);   // Re-enable the upload zone
    }
  }

  // ── Handle Sending a Chat Question ───────────────────────────────────────
  async function handleSendMessage(question) {
    const userMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await askQuestion(question);
      const assistantMessage = {
        role:    "assistant",
        content:  response.answer,
        sources:  response.sources || [],
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role:    "assistant",
        content: `Sorry, something went wrong: ${error.message}`,
        sources:  [],
        isError:  true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  // ── Handle Document Click ─────────────────────────────────────────────────
  function handleDocumentClick(docName) {
    // Toggle: clicking the active doc deselects it
    setActiveDocument((prev) => (prev === docName ? null : docName));
  }

  // ── Handle Clear Chat ─────────────────────────────────────────────────────
  function handleClearChat() {
    setMessages([]);
    setInputValue("");
  }

  // ── Handle Summarize (Phase 14) ───────────────────────────────────────────
  async function handleSummarize() {
    if (!activeDocument) return;

    // Add a loading message
    const loadingMsg = {
      role: "assistant",
      content: `✨ Generating summary for "${activeDocument}"... Please wait.`,
      sources: [],
    };
    setMessages((prev) => [...prev, loadingMsg]);
    setIsLoading(true);

    try {
      const result = await summarizeDocument(activeDocument);

      // Build a rich formatted summary message
      let content = `## 📄 Summary: ${activeDocument}\n\n`;
      content += `${result.summary}\n\n`;

      if (result.key_points && result.key_points.length > 0) {
        content += `**Key Points:**\n`;
        result.key_points.forEach((pt) => {
          content += `• ${pt}\n`;
        });
        content += "\n";
      }

      if (result.main_topics) {
        content += `**Main Topics:** ${result.main_topics}`;
      }

      const summaryMsg = {
        role:    "assistant",
        content: content.trim(),
        sources: [],
        isSummary: true,
      };
      // Replace loading message with real summary
      setMessages((prev) => [...prev.slice(0, -1), summaryMsg]);

    } catch (error) {
      const errorMsg = {
        role:    "assistant",
        content: `Sorry, failed to summarize "${activeDocument}": ${error.message}`,
        sources: [],
        isError: true,
      };
      setMessages((prev) => [...prev.slice(0, -1), errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDeleteDocument(docName) {
    try {
      const response = await deleteDocument(docName);
      setDocuments((prev) => prev.filter((doc) => doc.name !== docName));
      if (activeDocument === docName) {
        setActiveDocument(null);
      }
      if (response?.message) {
        console.log(`[INFO] Deleted document: ${response.message}`);
      }
    } catch (error) {
      setUploadError(error.message || "Failed to delete document.");
      console.error("[ERROR] Delete failed:", error.message);
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="app">
      {/* Top navigation bar */}
      <Header
        backendStatus={backendStatus}
        onMenuToggle={() => setMobileSidebarOpen((prev) => !prev)}
        showMenuButton={true}
      />

      {/* 2-panel body */}
      <div className={`app-body ${mobileSidebarOpen ? "mobile-sidebar-open" : ""}`}>
        {mobileSidebarOpen && (
          <button
            type="button"
            className="mobile-sidebar-backdrop"
            onClick={() => setMobileSidebarOpen(false)}
            aria-label="Close document panel"
          />
        )}

        <div className="sidebar-shell">
          {/* LEFT: Sidebar — document upload + list */}
          <Sidebar
            documents={documents}
            activeDocument={activeDocument}
            onDocumentClick={(docName) => {
              handleDocumentClick(docName);
              setMobileSidebarOpen(false);
            }}
            onUpload={handleUpload}
            onDelete={handleDeleteDocument}
            onSummarize={handleSummarize}
            uploadDisabled={isUploading}
            uploadError={uploadError}
          />
        </div>

        <div className="chat-panel">
          {/* RIGHT: Chat area — messages + input */}
          <ChatArea
            messages={messages}
            isLoading={isLoading}
            hasDocuments={documents.filter(d => d.status === "ready" || d.status === "indexed").length > 0}
            onSendMessage={handleSendMessage}
            inputValue={inputValue}
            onInputChange={setInputValue}
            onClearChat={handleClearChat}
          />
        </div>

        {/* Invisible scroll anchor at end of messages */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
