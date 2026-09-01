// components/Sidebar.jsx — Phase 4
// Left panel of the DocuMind AI interface.
//
// Phase 4 additions:
//   - Real drag-and-drop PDF upload (dragenter, dragover, dragleave, drop events)
//   - File input onChange wired to onUpload prop
//   - Client-side validation (type check, 16 MB size check) before sending to server
//   - Visual drag-over highlight state
//   - Upload error toast shown inline
//
// Props:
//   documents:        array  — [{name, size_mb, status, pages?, chunks?}]
//   activeDocument:   string — name of the currently selected document
//   onDocumentClick:  fn(docName) — called when user clicks a document
//   onUpload:         fn(File)    — called with the File object to upload
//   onSummarize:      fn()        — called when Summarize button is clicked
//   uploadDisabled:   bool        — true while a document is being processed
//   uploadError:      string|null — error message to show in upload zone

import { useState, useRef } from "react";

// Maximum file size we accept on the client side (16 MB)
// This matches the backend's MAX_UPLOAD_SIZE_BYTES setting.
const MAX_FILE_SIZE_BYTES = 16 * 1024 * 1024;

export default function Sidebar({
  documents = [],
  activeDocument = null,
  onDocumentClick = () => {},
  onUpload = () => {},
  onDelete = () => {},
  onSummarize = () => {},
  uploadDisabled = false,
  uploadError = null,
}) {
  // Track whether the user is dragging a file over the drop zone
  const [isDragOver, setIsDragOver] = useState(false);

  // Track client-side validation errors (before sending to server)
  const [localError, setLocalError] = useState(null);

  // Ref to the hidden file input so we can trigger it programmatically
  const fileInputRef = useRef(null);

  // ── Client-side validation ─────────────────────────────────────────────────
  // We validate here BEFORE calling onUpload so the user gets instant feedback.
  // The backend will also validate — this is just a faster UX check.
  function validateAndUpload(file) {
    setLocalError(null); // Clear any previous error

    // Check 1: Must be a PDF by MIME type or extension
    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setLocalError(`"${file.name}" is not a PDF. Only PDF files are accepted.`);
      return;
    }

    // Check 2: Must not exceed 16 MB
    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setLocalError(`File is too large (${sizeMB} MB). Maximum allowed size is 16 MB.`);
      return;
    }

    // All checks passed — hand the File object to the parent (App.jsx)
    onUpload(file);
  }

  // ── Drag-and-Drop Event Handlers ───────────────────────────────────────────

  function handleDragEnter(e) {
    e.preventDefault();
    e.stopPropagation();
    if (!uploadDisabled) setIsDragOver(true);
  }

  function handleDragOver(e) {
    // Prevent the browser's default behaviour (which is to open the file)
    e.preventDefault();
    e.stopPropagation();
    if (!uploadDisabled) setIsDragOver(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (uploadDisabled) return;

    // e.dataTransfer.files is a FileList — grab the first file
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndUpload(files[0]);
    }
  }

  // ── File Input onChange Handler ────────────────────────────────────────────
  function handleFileInputChange(e) {
    const file = e.target.files?.[0];
    if (file) {
      validateAndUpload(file);
    }
    // Reset the input so the same file can be re-uploaded if needed
    e.target.value = "";
  }

  // Use the server error if no local error is present
  const displayError = localError || uploadError;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <aside className="sidebar" role="complementary" aria-label="Document panel">

      {/* ── Section 1: Upload Zone ─────────────────────────────── */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">
          <span aria-hidden="true">📁</span> Upload Document
        </div>

        {/* Drop zone — handles both drag-and-drop and click-to-browse */}
        <div
          className={[
            "upload-zone",
            isDragOver   ? "drag-over"  : "",
            uploadDisabled ? "disabled" : "",
          ].join(" ")}
          role="button"
          tabIndex={uploadDisabled ? -1 : 0}
          aria-label="Upload PDF — drag and drop or click to browse"
          aria-disabled={uploadDisabled}
          // Drag events
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          // Click opens the hidden file input
          onClick={() => {
            if (!uploadDisabled) fileInputRef.current?.click();
          }}
          // Keyboard: Enter or Space also opens the file picker
          onKeyDown={(e) => {
            if ((e.key === "Enter" || e.key === " ") && !uploadDisabled) {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
        >
          {/* Hidden native file input */}
          <input
            ref={fileInputRef}
            id="pdf-upload-input"
            type="file"
            accept=".pdf"
            className="upload-input"
            style={{ display: "none" }}   // hidden — triggered programmatically
            disabled={uploadDisabled}
            aria-label="Select PDF file"
            onChange={handleFileInputChange}
          />

          {/* Icon — changes based on state */}
          <span className="upload-icon" aria-hidden="true">
            {uploadDisabled ? "⏳" : isDragOver ? "📂" : "📄"}
          </span>

          {/* Primary text */}
          <div className="upload-zone-text">
            {uploadDisabled
              ? "Uploading document…"
              : isDragOver
              ? "Drop your PDF here"
              : "Drag & Drop PDF here"}
          </div>

          {/* Hint text */}
          <div className="upload-zone-hint">
            {uploadDisabled
              ? "Please wait while the file is uploaded"
              : isDragOver
              ? "Release to upload"
              : <>or <span>browse files</span> · PDF · Max 16 MB</>}
          </div>
        </div>

        {/* Inline error message below the drop zone */}
        {displayError && (
          <div className="upload-error" role="alert">
            <span aria-hidden="true">⚠️</span> {displayError}
          </div>
        )}
      </div>

      {/* ── Section 2: Document List Header ───────────────────── */}
      <div className="sidebar-section" style={{ paddingBottom: "var(--space-sm)" }}>
        <div className="sidebar-section-title">
          <span aria-hidden="true">📚</span>
          Uploaded Documents
          {documents.length > 0 && (
            <span style={{
              marginLeft: "auto",
              background: "var(--color-primary-glow)",
              border: "1px solid rgba(99,102,241,0.3)",
              borderRadius: "var(--radius-full)",
              padding: "1px 8px",
              fontSize: "0.65rem",
              color: "var(--color-primary-light)",
              fontWeight: 700,
            }}>
              {documents.length}
            </span>
          )}
        </div>
      </div>

      {/* ── Scrollable Document List ───────────────────────────── */}
      <div className="document-list" role="list" aria-label="Uploaded documents">
        {documents.length === 0 ? (
          <div style={{
            textAlign: "center",
            padding: "var(--space-lg)",
            color: "var(--color-text-muted)",
            fontSize: "0.8rem",
            lineHeight: 1.6,
          }}>
            No documents yet.<br />
            Upload a PDF to get started.
          </div>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.name}
              className={`document-item ${activeDocument === doc.name ? "active" : ""}`}
              role="listitem"
              onClick={() => onDocumentClick(doc.name)}
              onKeyDown={(e) => {
                if (e.key === "Enter") onDocumentClick(doc.name);
              }}
              tabIndex={0}
              aria-label={`Document: ${doc.name}, ${doc.size_mb} MB, status: ${doc.status}`}
              aria-pressed={activeDocument === doc.name}
            >
              <span className="document-icon" aria-hidden="true">📄</span>

              <div className="document-info">
                <div className="document-name" title={doc.name}>
                  {doc.name}
                </div>
                <div className="document-meta">
                  {/* Phase 5: pages comes from PyMuPDF extraction */}
                  {doc.pages  ? `${doc.pages} pages` : `${doc.size_mb || "?"} MB`}
                  {doc.chunks ? ` · ${doc.chunks} chunks` : ""}
                </div>
              </div>

              <button
                type="button"
                className="document-delete-btn"
                aria-label={`Delete ${doc.name}`}
                title={`Delete ${doc.name}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(doc.name);
                }}
              >
                🗑
              </button>

              {/* Coloured status dot */}
              <div
                className={`document-status ${doc.status ?? "ready"}`}
                title={doc.status === "loading" ? "Uploading…" : "Ready"}
                aria-hidden="true"
              />
            </div>
          ))
        )}
      </div>

      {/* ── Summarize Button (Phase 14) ────────────────────────── */}
      <button
        className="summarize-btn"
        onClick={onSummarize}
        disabled={!activeDocument}
        title={activeDocument ? `Summarize ${activeDocument}` : "Select a document first"}
        aria-label={activeDocument ? `Summarize ${activeDocument}` : "Select a document to enable summarization"}
      >
        <span aria-hidden="true">✨</span>
        Summarize Document
      </button>

    </aside>
  );
}
