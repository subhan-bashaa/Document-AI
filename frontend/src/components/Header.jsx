// components/Header.jsx
// The top navigation bar of DocuMind AI.
//
// Shows:
// - App logo + name + subtitle
// - Mobile menu icon for the document drawer

export default function Header({ backendStatus = "checking", onMenuToggle = () => {}, showMenuButton = false }) {
  const statusConfig = {
    checking:     { label: "Connecting...",   dotClass: "checking",     text: "checking"     },
    connected:    { label: "Backend Online",  dotClass: "connected",    text: "connected"    },
    disconnected: { label: "Backend Offline", dotClass: "disconnected", text: "disconnected" },
  };

  const { label, dotClass, text } = statusConfig[backendStatus] ?? statusConfig.checking;

  return (
    <header className="app-header" role="banner">
      <div className="header-left-group">
        {showMenuButton && (
          <button
            type="button"
            className="mobile-menu-button"
            onClick={onMenuToggle}
            aria-label="Toggle document panel"
            title="Toggle document panel"
          >
            ☰
          </button>
        )}

        <div className="header-brand">
          <div className="header-logo" aria-hidden="true">🧠</div>
          <div>
            <div className="header-title">DocuMind AI</div>
            <div className="header-subtitle">Responsible-first Document Research Assistant</div>
          </div>
        </div>
      </div>

    </header>
  );
}
