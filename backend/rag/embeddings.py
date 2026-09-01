# rag/embeddings.py – Embedding generation module (Phase 7)
#
# EMBEDDING STRATEGY:
#   When EMBEDDING_MODEL=local (default), uses ChromaDB's built-in
#   ONNX embedding model (all-MiniLM-L6-v2, 384 dimensions).
#   This runs entirely on your CPU — no API key, no quota limits.
#
#   When EMBEDDING_MODEL=models/gemini-embedding-001 (or similar),
#   falls back to Google Gemini embedding API.

from config import config

# ── Singleton: local embedding function ─────────────────────────────────────
# Loaded once, reused for every request.
_local_ef = None


def _get_local_ef():
    """Return ChromaDB's built-in local ONNX embedding function (singleton)."""
    global _local_ef
    if _local_ef is None:
        from chromadb.utils import embedding_functions
        print("[INFO] Loading local ONNX embedding model (all-MiniLM-L6-v2)...")
        _local_ef = embedding_functions.DefaultEmbeddingFunction()
        print("[INFO] Local embedding model ready.")
    return _local_ef


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate vector embeddings for a list of text strings (document chunks).

    Uses local ONNX model when EMBEDDING_MODEL=local, else Gemini API.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (same order as texts).
    """
    if not texts:
        return []

    _validate_texts(texts)

    if config.EMBEDDING_MODEL == "local":
        return _embed_local(texts)
    else:
        return _embed_gemini(texts, task_type="retrieval_document")


def generate_query_embedding(query: str) -> list[float]:
    """
    Generate a single embedding vector for a user's search query.

    Args:
        query: The user's question string (must be non-empty).

    Returns:
        A single embedding vector (list of floats).
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    if config.EMBEDDING_MODEL == "local":
        vecs = _embed_local([query.strip()])
        return vecs[0]
    else:
        return _embed_gemini_single(query.strip())


# ── Local Embedding (ChromaDB ONNX, no API) ──────────────────────────────────

def _embed_local(texts: list[str]) -> list[list[float]]:
    ef = _get_local_ef()
    print(f"[INFO] Local embedding: {len(texts)} texts...")
    # ChromaDB's EF returns a list of lists
    embeddings = ef(texts)
    print(f"[INFO] Local embedding complete: {len(embeddings)} vectors (dim={len(embeddings[0])})")
    return embeddings


# ── Gemini Embedding (API-based, may have quota limits) ──────────────────────

_BATCH_SIZE = 100


def _embed_gemini(texts: list[str], task_type: str = "retrieval_document") -> list[list[float]]:
    import google.generativeai as genai
    _configure_genai()
    all_embeddings = []
    for batch_start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[batch_start: batch_start + _BATCH_SIZE]
        print(f"[INFO] Gemini embedding batch {batch_start // _BATCH_SIZE + 1} ({len(batch)} texts)...")
        result = genai.embed_content(
            model=config.EMBEDDING_MODEL,
            content=batch,
            task_type=task_type,
        )
        all_embeddings.extend(result["embedding"])
    return all_embeddings


def _embed_gemini_single(query: str) -> list[float]:
    import google.generativeai as genai
    _configure_genai()
    result = genai.embed_content(
        model=config.EMBEDDING_MODEL,
        content=query,
        task_type="retrieval_query",
    )
    return result["embedding"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _configure_genai() -> None:
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in backend/.env")
    import google.generativeai as genai
    genai.configure(api_key=config.GEMINI_API_KEY)


def _validate_texts(texts: list[str]) -> None:
    for i, text in enumerate(texts):
        if not text or not text.strip():
            raise ValueError(
                f"texts[{i}] is empty. All texts must be non-empty strings."
            )
