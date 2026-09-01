// components/LoadingDots.jsx
// Reusable animated loading indicator.
// Used in: chat typing indicator, document processing status.

export default function LoadingDots({ label = "Searching documents..." }) {
  return (
    <div className="typing-indicator" role="status" aria-label={label}>
      <div className="typing-dot" />
      <div className="typing-dot" />
      <div className="typing-dot" />
    </div>
  );
}
