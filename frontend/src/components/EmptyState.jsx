// components/EmptyState.jsx
// Shown in the chat area when no documents have been uploaded yet.
// Guides the user to upload a PDF to get started.

export default function EmptyState() {
  return (
    <div className="empty-state animate-fade-in" role="status" aria-label="No documents uploaded">
      {/* Decorative icon */}
      <div className="empty-state-icon" aria-hidden="true">📄</div>

      <h2 className="empty-state-title">Responsible document search starts here</h2>

      <p className="empty-state-text">
        Upload a PDF to ground your questions in trusted source material.
        Answers are generated only from the uploaded document set,
        helping reduce hallucination and improve traceability.
      </p>

      {/* Feature highlights */}
      <div style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-sm)",
        marginTop: "var(--space-md)",
        width: "100%",
        maxWidth: "320px"
      }}>
        {[
          { icon: "🔍", text: "Grounded retrieval from uploaded document pages" },
          { icon: "🤖", text: "Responsible AI answers based only on source material" },
          { icon: "📍", text: "Source-backed answers with page references" },
          { icon: "🛡️", text: "Trust-first design to reduce hallucination" },
        ].map(({ icon, text }) => (
          <div
            key={text}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-sm)",
              padding: "var(--space-sm) var(--space-md)",
              background: "var(--color-bg-surface)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--color-border)",
              fontSize: "0.8rem",
              color: "var(--color-text-secondary)",
            }}
          >
            <span aria-hidden="true">{icon}</span>
            <span>{text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
