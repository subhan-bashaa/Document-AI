# config.py – Centralized configuration for DocuMind AI backend
#
# WHY THIS FILE EXISTS:
# Instead of calling os.getenv() scattered across every file,
# we read ALL config here once. Every other module imports from here.
# If a required variable is missing, the app refuses to start with a clear message.

import os
from dotenv import load_dotenv

# Load .env file FIRST before reading any variables
load_dotenv()


class Config:
    """
    Central configuration class.
    All settings come from environment variables (set in .env).
    Never hard-code values here — always use os.getenv().
    """

    # ── Google Gemini API ────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # ── Groq API (used for fast LLM generation) ──────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # ── Flask Settings ───────────────────────────────────────────────────────
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = FLASK_ENV == "development"

    # ── File Upload ──────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(16 * 1024 * 1024)))
    MAX_UPLOAD_SIZE_MB: float = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
    ALLOWED_EXTENSIONS: set = {"pdf"}

    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "documents")

    # ── ChromaDB Vector Store ────────────────────────────────────────────────
    CHROMA_DB_PATH: str = os.getenv(
        "CHROMA_DB_PATH",
        os.path.join(os.path.dirname(__file__), "vectorstore", "chroma_db")
    )

    # ── RAG Settings ─────────────────────────────────────────────────────────
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

    # ── Embedding Settings ────────────────────────────────────────────────────
    # Set to "local" to use ChromaDB's built-in ONNX embedding (no API needed).
    # Otherwise set to a Gemini model name like "models/gemini-embedding-001".
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "local")

    @classmethod
    def validate(cls) -> None:
        """Check required config. Called once at app startup."""
        errors = []

        has_gemini = bool(cls.GEMINI_API_KEY and cls.GEMINI_API_KEY != "your_gemini_api_key_here")
        has_groq   = bool(cls.GROQ_API_KEY)

        if not has_gemini and not has_groq:
            errors.append(
                "No LLM API key configured.\n"
                "  → Set GROQ_API_KEY in backend/.env (get one free at https://console.groq.com)\n"
                "  → Or set GEMINI_API_KEY from https://aistudio.google.com/app/apikey"
            )

        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)

        if errors:
            error_msg = "\n\n".join(errors)
            raise ValueError(
                f"\n{'='*60}\n"
                f"DocuMind AI — Configuration Error\n"
                f"{'='*60}\n"
                f"{error_msg}\n"
                f"{'='*60}\n"
            )

    @classmethod
    def summary(cls) -> dict:
        """Return a safe summary of current config (no secrets)."""
        return {
            "flask_env":         cls.FLASK_ENV,
            "flask_port":        cls.FLASK_PORT,
            "max_upload_mb":     cls.MAX_UPLOAD_SIZE_MB,
            "top_k_results":     cls.TOP_K_RESULTS,
            "chunk_size":        cls.CHUNK_SIZE,
            "chunk_overlap":     cls.CHUNK_OVERLAP,
            "embedding_model":   cls.EMBEDDING_MODEL,
            "groq_configured":   bool(cls.GROQ_API_KEY),
            "gemini_configured": bool(cls.GEMINI_API_KEY and cls.GEMINI_API_KEY != "your_gemini_api_key_here"),
            "llm_provider":      "groq" if cls.GROQ_API_KEY else "gemini",
        }


# Create a single instance used throughout the app
config = Config()
