# rag/retriever.py – Semantic retrieval module (Phase 9)
#
# WHY THIS FILE EXISTS:
# When a user asks a question, we need to find the most relevant chunks
# from ChromaDB to pass as context to Gemini. This file handles that:
#   1. Embed the user's question using the same model used for documents
#      (but with task_type="retrieval_query" for better accuracy)
#   2. Ask ChromaDB for the top-K chunks closest to the query vector
#   3. Return those chunks so the generator can build a RAG prompt
#
# IMPORTANT: We use generate_query_embedding() (not generate_embeddings())
# because the query needs a different task_type than document chunks.

from rag.embeddings  import generate_query_embedding
from rag.vectorstore import query_chunks
from config          import config


def retrieve_relevant_chunks(query: str, top_k: int = None,
                             source_filter: str = None) -> list[dict]:
    """
    Find the top-k most semantically relevant document chunks for a query.

    Pipeline:
      1. Embed the query string using task_type="retrieval_query"
      2. Search ChromaDB for the nearest neighbours in vector space
      3. Return ranked results with text, source, page, and distance score

    Args:
        query:         The user's question string (must be non-empty).
        top_k:         Number of top results to return.
                       Defaults to config.TOP_K_RESULTS (set in .env, default 5).
        source_filter: If provided, restrict search to chunks from this
                       document filename (e.g., "college_handbook.pdf").
                       None means search across ALL uploaded documents.

    Returns:
        List of chunk dicts ordered by relevance (most relevant first):
        [
            {
                "text":     "The admission requirements are ...",
                "source":   "college_handbook.pdf",
                "page":     4,
                "distance": 0.23   # cosine distance; lower = more similar
            },
            ...
        ]
        Returns an empty list if no documents have been indexed yet.

    Raises:
        ValueError: If query is empty or whitespace-only.
        google.api_core.exceptions.GoogleAPIError: If the embedding API call fails.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string.")

    if top_k is None:
        top_k = config.TOP_K_RESULTS

    print(f"[Phase 9] Retrieving top-{top_k} chunks for query: "
          f"\"{query[:80]}{'...' if len(query) > 80 else ''}\"")

    # Step 1: Embed the query with task_type="retrieval_query"
    query_embedding = generate_query_embedding(query.strip())

    # Step 2: Search ChromaDB for nearest neighbours
    chunks = query_chunks(
        query_embedding=query_embedding,
        top_k=top_k,
        source_filter=source_filter,
    )

    print(f"[Phase 9] Retrieved {len(chunks)} relevant chunks.")
    for i, chunk in enumerate(chunks):
        print(f"  [{i+1}] source={chunk['source']} page={chunk['page']} "
              f"distance={chunk['distance']}")

    return chunks
