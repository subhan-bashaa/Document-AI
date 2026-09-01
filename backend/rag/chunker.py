# rag/chunker.py – Text chunking module (Phase 6)
#
# WHY THIS FILE EXISTS:
# Large language models have a fixed context window — they can't read an
# entire PDF at once. ChromaDB also works best with small, focused pieces
# of text. We split each page's text into overlapping "chunks" so that:
#
#   1. No single chunk is too large for an embedding model.
#   2. Overlap between chunks prevents context from being cut off at a
#      boundary — a sentence that spans two chunks is still captured.
#   3. Each chunk carries metadata (source, page, chunk_id) so we can
#      always trace an answer back to the exact page it came from.
#
# Algorithm: sliding-window character chunking
#   - Walk through the text in steps of (chunk_size - overlap)
#   - Each window is chunk_size characters long
#   - Adjacent windows share `overlap` characters
#
# Example with chunk_size=20, overlap=5, text="ABCDEFGHIJKLMNOPQRSTUVWXYZ":
#   chunk 0: ABCDEFGHIJKLMNOPQRST   (chars 0-19)
#   chunk 1: PQRSTUVWXYZ...         (chars 15-34)  overlaps 5 chars with chunk 0
#
# Config values (chunk_size, overlap) come from config.py / .env
# so they can be tuned without code changes.


def chunk_pages(pages: list[dict], chunk_size: int = 1000, overlap: int = 150) -> list[dict]:
    """
    Split extracted page text into overlapping chunks for embedding.

    Each input page dict (from loader.py) looks like:
        {"text": "...", "page": 3, "source": "report.pdf"}

    Each output chunk dict looks like:
        {
            "text":     "...",                    <- chunk text (<= chunk_size chars)
            "source":   "report.pdf",             <- original filename
            "page":     3,                        <- 1-based page number
            "chunk_id": "report.pdf_p3_c0"        <- unique ID for ChromaDB
        }

    Args:
        pages:      List of page dicts produced by loader.load_pdf().
        chunk_size: Maximum number of characters per chunk (default 1000).
        overlap:    Number of characters shared between adjacent chunks (default 150).
                    Must be less than chunk_size.

    Returns:
        List of chunk dicts, ordered by (page, chunk_index).
        Returns an empty list if pages is empty.

    Raises:
        ValueError: If chunk_size <= 0 or overlap >= chunk_size.
    """

    # ── Input validation ──────────────────────────────────────────────────────
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be > 0, got {chunk_size}")
    if overlap < 0:
        raise ValueError(f"overlap must be >= 0, got {overlap}")
    if overlap >= chunk_size:
        raise ValueError(
            f"overlap ({overlap}) must be less than chunk_size ({chunk_size}). "
            f"Otherwise chunks would never advance forward."
        )

    if not pages:
        return []

    # ── Sliding-window chunking ───────────────────────────────────────────────
    all_chunks = []

    # How far to advance the window start each step
    step = chunk_size - overlap

    for page_dict in pages:
        text   = page_dict["text"]
        page   = page_dict["page"]
        source = page_dict["source"]

        # If the entire page fits in one chunk, no splitting needed
        if len(text) <= chunk_size:
            chunk_id = _make_chunk_id(source, page, 0)
            all_chunks.append({
                "text":     text,
                "source":   source,
                "page":     page,
                "chunk_id": chunk_id,
            })
            continue

        # Slide the window across the page text
        chunk_index = 0
        start = 0

        while start < len(text):
            end        = start + chunk_size
            chunk_text = text[start:end].strip()

            # Only add non-empty chunks (strip can make short ones empty)
            if chunk_text:
                chunk_id = _make_chunk_id(source, page, chunk_index)
                all_chunks.append({
                    "text":     chunk_text,
                    "source":   source,
                    "page":     page,
                    "chunk_id": chunk_id,
                })
                chunk_index += 1

            # Advance by step; stop once we've covered the full text
            if end >= len(text):
                break
            start += step

    print(f"[INFO] Chunking complete: {len(pages)} pages -> {len(all_chunks)} chunks "
          f"(size={chunk_size}, overlap={overlap})")

    return all_chunks


# ── Helper ─────────────────────────────────────────────────────────────────────

def _make_chunk_id(source: str, page: int, chunk_index: int) -> str:
    """
    Build a deterministic, human-readable chunk ID.

    Format:  "<source>_p<page>_c<chunk_index>"
    Example: "college_handbook.pdf_p3_c0"

    WHY: ChromaDB uses this ID to detect duplicates.
    Using a deterministic ID means re-uploading the same PDF
    replaces existing chunks rather than creating duplicates.
    """
    safe_source = source.replace(" ", "_")
    return f"{safe_source}_p{page}_c{chunk_index}"
