# rag/generator.py – Answer generation using Groq (Phases 10 & 11)
#
# Uses Groq API for ultra-fast LLM inference (Llama 3.3 70B).
# Falls back to Gemini if GROQ_API_KEY is not set.
#
# Phase 10: Calls the LLM to generate a grounded answer.
# Phase 11: Builds the RAG prompt that constrains the LLM to ONLY use
#           the provided context — no hallucination from training data.

from config import config

# Groq model availability varies by account and region.
# Some keys reject the hardcoded 70B model, so try a few known-safe options
# before falling back to Gemini.
_GROQ_MODEL_CANDIDATES = (
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
)
_GEMINI_MODEL = "models/gemini-2.5-flash"

# Maximum cosine distance to accept a retrieved chunk as relevant.
_MAX_DISTANCE_THRESHOLD = 0.7


def generate_answer(question: str, context_chunks: list[dict]) -> dict:
    """
    Generate a grounded answer using the configured LLM + retrieved document context.

    Phase 10: LLM API call.
    Phase 11: RAG prompt that prevents hallucination.

    Args:
        question:       The user's question string.
        context_chunks: List of relevant chunk dicts from retriever.py.
                        Each has: text, source, page, distance.

    Returns:
        {
            "answer":  "The eligibility requirements are ...",
            "sources": [{"document": "file.pdf", "page": 4}]
        }
    """
    if not question or not question.strip():
        raise ValueError("question must be a non-empty string.")

    # ── Phase 11: Filter low-relevance chunks ─────────────────────────────────
    relevant_chunks = [
        chunk for chunk in context_chunks
        if chunk.get("distance", 1.0) <= _MAX_DISTANCE_THRESHOLD
    ]

    print(f"[Phase 11] {len(relevant_chunks)}/{len(context_chunks)} chunks "
          f"passed relevance threshold (max distance: {_MAX_DISTANCE_THRESHOLD})")

    # ── Phase 11: Build the RAG prompt ────────────────────────────────────────
    prompt = _build_rag_prompt(question, relevant_chunks)

    # ── Phase 10: Call Groq or Gemini ─────────────────────────────────────────
    if config.GROQ_API_KEY:
        answer_text = _call_groq(prompt)
    else:
        answer_text = _call_gemini(prompt)

    # ── Build deduplicated source list ────────────────────────────────────────
    seen = set()
    sources = []
    for chunk in relevant_chunks:
        key = (chunk["source"], chunk["page"])
        if key not in seen:
            seen.add(key)
            sources.append({"document": chunk["source"], "page": chunk["page"]})

    return {"answer": answer_text, "sources": sources}


# ── Phase 11: RAG Prompt Builder ─────────────────────────────────────────────

def _build_rag_prompt(question: str, chunks: list[dict]) -> str:
    """Build the grounding prompt that constrains the LLM to document context."""

    if not chunks:
        return (
            "You are a helpful document assistant. A user asked:\n\n"
            f"Question: {question}\n\n"
            "No relevant content was found in the uploaded documents. "
            "Explain that the answer was not found and suggest uploading more relevant documents."
        )

    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Source {i}: {chunk['source']}, Page {chunk['page']}]\n{chunk['text']}"
        )
    context_block = "\n\n---\n\n".join(context_parts)

    return f"""You are DocuMind AI, an expert document research assistant. \
Answer questions based ONLY on the document excerpts below.

STRICT RULES:
1. Answer ONLY from the provided context. Do NOT use knowledge from your training data.
2. If the context lacks enough information, say: "I don't have enough information in the uploaded documents to answer this question."
3. Always cite your sources by mentioning the document name and page number.
4. Be concise and accurate. Do not make up details.
5. If multiple sources support the answer, mention all of them.

---
DOCUMENT CONTEXT:

{context_block}

---
USER QUESTION:

{question}

---
ANSWER (based only on the above context):"""


# ── LLM Callers ──────────────────────────────────────────────────────────────

def _call_groq(prompt: str) -> str:
    """Call Groq API for fast LLM inference with a safe fallback chain."""
    from groq import Groq
    client = Groq(api_key=config.GROQ_API_KEY)

    last_error = None
    for model_name in _GROQ_MODEL_CANDIDATES:
        try:
            print(f"[Phase 10] Calling Groq ({model_name})...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.1,
            )
            answer = response.choices[0].message.content.strip()
            print(f"[Phase 10] Groq response received ({len(answer)} chars).")
            return answer
        except Exception as exc:
            last_error = exc
            print(f"[Phase 10] Groq model '{model_name}' failed: {exc}")

    if config.GEMINI_API_KEY:
        print("[Phase 10] Groq unavailable; falling back to Gemini.")
        return _call_gemini(prompt)

    raise RuntimeError(
        f"All Groq models failed. Last error: {last_error}"
    ) from last_error


def _call_gemini(prompt: str) -> str:
    """Fall back to Gemini if no Groq key is set."""
    import google.generativeai as genai
    if not config.GEMINI_API_KEY:
        raise ValueError("Neither GROQ_API_KEY nor GEMINI_API_KEY is configured.")
    genai.configure(api_key=config.GEMINI_API_KEY)
    print(f"[Phase 10] Calling Gemini ({_GEMINI_MODEL})...")
    model = genai.GenerativeModel(model_name=_GEMINI_MODEL)
    response = model.generate_content(prompt)
    answer = response.text.strip() if response.text else "I couldn't generate an answer. Please try again."
    print(f"[Phase 10] Gemini response received ({len(answer)} chars).")
    return answer
