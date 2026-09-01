# rag/vectorstore.py – ChromaDB vector store module (Phase 8)
#
# WHY THIS FILE EXISTS:
# After Phase 7 converts text chunks into 768-dimensional vectors, we need
# somewhere persistent to store them so we can search them later without
# re-embedding every time a user asks a question.
#
# ChromaDB is a local-first vector database. It stores:
#   - The embedding vectors (for similarity search)
#   - The original text (returned with search results)
#   - Metadata (source filename, page number — so we can cite sources)
#   - A unique ID per chunk (for upsert / deduplication)
#
# HOW ChromaDB 1.x WORKS (API refresher):
#   - PersistentClient(path=...)  → auto-saves to disk; no .persist() needed
#   - client.get_or_create_collection(name, metadata={...})
#                                 → idempotent; safe to call on every startup
#   - collection.upsert(...)      → insert or update by ID; prevents duplicates
#   - collection.query(...)       → nearest-neighbour vector search
#   - collection.delete(...)      → remove by filter
#   - collection.count()          → total stored chunks
#
# IMPORTANT — ChromaDB 1.x vs 0.x:
#   The 0.x API used chromadb.Client() and required manual .persist() calls.
#   The 1.x API uses chromadb.PersistentClient() and persists automatically.
#   We pin to 1.x (see requirements.txt). Do NOT use the old 0.x API.
#
# COLLECTION DESIGN:
#   One collection named "documents" stores ALL chunks from ALL PDFs.
#   ChromaDB's metadata filtering lets us query chunks from a specific
#   document (e.g., where source == "report.pdf").
#
# EMBEDDING FUNCTION:
#   ChromaDB 1.x supports pluggable embedding functions, but we deliberately
#   pass embeddings manually. This keeps Phase 7 as the single source of
#   truth for our embedding model. ChromaDB then stores them as-is.

from typing import Optional
import chromadb
from chromadb.config import Settings

from config import config

# ── Collection configuration ───────────────────────────────────────────────────

# The single collection name used for all document chunks.
_COLLECTION_NAME = "documents"

# ChromaDB's cosine distance metric.
# Cosine similarity is standard for embedding-based semantic search.
# l2 (Euclidean) is also available but cosine works better for text.
_DISTANCE_METRIC = "cosine"

# Module-level singleton — the client and collection are created once
# and reused for every request in the process lifetime.
_client: Optional[chromadb.PersistentClient] = None
_collection = None


# ── Public API ─────────────────────────────────────────────────────────────────

def get_collection():
    """
    Return the ChromaDB collection, creating it if it doesn't exist yet.

    Uses a module-level singleton so we don't re-open the database on
    every request (opening is cheap, but unnecessary round-trips add up).

    Returns:
        chromadb.Collection: The persistent "documents" collection.
    """
    global _client, _collection

    if _collection is None:
        _client = chromadb.PersistentClient(
            path=config.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),   # disable telemetry
        )

        _collection = _client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": _DISTANCE_METRIC},
        )

        print(f"[INFO] ChromaDB collection '{_COLLECTION_NAME}' ready "
              f"(path={config.CHROMA_DB_PATH}, chunks={_collection.count()})")

    return _collection


def add_chunks(chunks: list[dict], embeddings: list[list[float]]) -> int:
    """
    Upsert a list of text chunks and their precomputed embeddings into ChromaDB.

    Uses upsert (not add) so re-uploading the same PDF replaces its chunks
    instead of creating duplicates.  The deterministic chunk_id produced by
    chunker.py is what makes deduplication work.

    Args:
        chunks:     List of chunk dicts from chunker.chunk_pages().
                    Each dict must have: text, source, page, chunk_id.
        embeddings: Parallel list of embedding vectors from embeddings.py.
                    len(embeddings) must equal len(chunks).

    Returns:
        Number of chunks upserted.

    Raises:
        ValueError: If lengths don't match or any required field is missing.
    """
    if not chunks:
        print("[INFO] add_chunks called with empty list — nothing to store.")
        return 0

    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings. "
            "They must be parallel lists."
        )

    # Validate required fields before touching the database
    for i, chunk in enumerate(chunks):
        for field in ("text", "source", "page", "chunk_id"):
            if field not in chunk:
                raise ValueError(
                    f"chunks[{i}] is missing required field '{field}'. "
                    f"Got keys: {list(chunk.keys())}"
                )

    collection = get_collection()

    # ChromaDB expects four parallel lists:
    #   ids        → unique string IDs (used for upsert deduplication)
    #   embeddings → the precomputed vectors
    #   documents  → the raw text (returned in query results)
    #   metadatas  → dict of filterable metadata per chunk
    ids        = [c["chunk_id"] for c in chunks]
    documents  = [c["text"]     for c in chunks]
    metadatas  = [{"source": c["source"], "page": c["page"]} for c in chunks]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"[INFO] ChromaDB upsert complete: {len(chunks)} chunks stored. "
          f"Total in collection: {collection.count()}")

    return len(chunks)


def query_chunks(query_embedding: list[float], top_k: int = 5,
                 source_filter: Optional[str] = None) -> list[dict]:
    """
    Find the top-k most semantically similar chunks to a query embedding.

    Args:
        query_embedding: The 768-float query vector from embeddings.py.
        top_k:           How many results to return (default 5).
        source_filter:   If set, only return chunks from this source filename
                         (e.g., "college_handbook.pdf").

    Returns:
        List of result dicts, ordered by relevance (closest first):
        [
            {
                "text":     "...",              ← original chunk text
                "source":   "report.pdf",       ← filename
                "page":     4,                  ← page number (1-based)
                "distance": 0.23,               ← cosine distance (0=identical)
            },
            ...
        ]
        Returns an empty list if the collection is empty.
    """
    collection = get_collection()

    if collection.count() == 0:
        print("[WARN] query_chunks called but collection is empty. "
              "Upload and index a document first.")
        return []

    # Build optional where-filter for source-specific search
    where = {"source": source_filter} if source_filter else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),   # can't request more than exist
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # Unpack the nested lists ChromaDB returns
    # results["documents"][0]  → list of text strings for query 0
    # results["metadatas"][0]  → list of metadata dicts for query 0
    # results["distances"][0]  → list of cosine distances for query 0
    output = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "text":     text,
            "source":   meta.get("source", "unknown"),
            "page":     meta.get("page",   0),
            "distance": round(dist, 4),
        })

    return output


def delete_document_chunks(source: str) -> int:
    """
    Delete all chunks belonging to a specific document from ChromaDB.

    Useful when a document is deleted from the system or needs to be re-indexed.

    Args:
        source: The filename of the document (e.g., "college_handbook.pdf").

    Returns:
        Number of chunks deleted (approximate — ChromaDB doesn't return
        an exact count from .delete()).
    """
    collection = get_collection()

    # Count before so we can report how many were removed
    before = collection.count()

    collection.delete(where={"source": source})

    after = collection.count()
    deleted = before - after

    print(f"[INFO] Deleted chunks for '{source}': {deleted} removed "
          f"({after} remaining in collection).")

    return deleted


def get_collection_stats() -> dict:
    """
    Return a summary of what is stored in the ChromaDB collection.

    Returns:
        {
            "total_chunks": int,
            "collection_name": str,
            "db_path": str,
        }
    """
    collection = get_collection()
    return {
        "total_chunks":    collection.count(),
        "collection_name": _COLLECTION_NAME,
        "db_path":         config.CHROMA_DB_PATH,
    }
