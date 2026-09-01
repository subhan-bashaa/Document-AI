# routes/chat.py – Chat/question-answering endpoints
#
# POST /api/chat
# Accepts a user question, retrieves relevant document chunks from ChromaDB,
# and returns a grounded AI answer from Gemini with cited sources.
#
# Phase 9:  retrieve_relevant_chunks() — semantic search in ChromaDB
# Phase 10: generate_answer()          — Gemini API call
# Phase 11: RAG prompt built inside generator.py

from flask import Blueprint, jsonify, request

from rag.retriever import retrieve_relevant_chunks   # Phase 9
from rag.generator import generate_answer            # Phases 10 & 11
from config        import config

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    POST /api/chat

    Request body (JSON):
        {
            "question": "What are the eligibility requirements?",
            "source_filter": "college_handbook.pdf"  (optional)
        }

    Response (JSON):
        {
            "answer":  "The eligibility requirements are ...",
            "sources": [
                {"document": "college_handbook.pdf", "page": 4}
            ],
            "status":  "success"
        }

    Error responses:
        400 – Missing or empty question
        503 – No documents indexed yet (upload a PDF first)
        500 – Internal error (Gemini API failure, etc.)
    """
    # ── Step 1: Parse JSON body ───────────────────────────────────────────────
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error":  "Request body must be JSON with a 'question' field.",
            "status": "error"
        }), 400

    # ── Step 2: Validate the question field ───────────────────────────────────
    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error":  "The 'question' field is required and cannot be empty.",
            "status": "error"
        }), 400

    if len(question) > 2000:
        return jsonify({
            "error":  "Question is too long. Maximum 2000 characters allowed.",
            "status": "error"
        }), 400

    # Optional: restrict search to a specific document
    source_filter = data.get("source_filter", None)

    # ── Step 3: Phase 9 — Retrieve relevant chunks from ChromaDB ─────────────
    try:
        chunks = retrieve_relevant_chunks(
            query=question,
            top_k=config.TOP_K_RESULTS,
            source_filter=source_filter,
        )
    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}")
        return jsonify({
            "error":  "Failed to search documents. Please make sure you have uploaded a PDF first.",
            "status": "error"
        }), 503

    # ── Step 4: Phases 10 & 11 — Generate answer with Gemini ─────────────────
    try:
        result = generate_answer(
            question=question,
            context_chunks=chunks,
        )
    except Exception as e:
        print(f"[ERROR] Generation failed: {e}")
        return jsonify({
            "error":  f"Failed to generate answer: {str(e)}",
            "status": "error"
        }), 500

    # ── Step 5: Return the grounded answer and sources ────────────────────────
    return jsonify({
        "answer":  result["answer"],
        "sources": result["sources"],
        "status":  "success",
    }), 200
