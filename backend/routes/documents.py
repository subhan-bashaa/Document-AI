# routes/documents.py – Document management endpoints
#
# GET  /api/documents              – List all uploaded documents
# POST /api/documents/upload       – Upload and save a new PDF (Phase 4–8)
# POST /api/documents/{id}/summary – Summarize a document (Phase 14)
#
# Phase 5: After saving the file, extract text with PyMuPDF.
#          Page count is now returned in both upload and list responses.
# Phase 6: Extracted pages are chunked immediately after extraction.
#          Chunk count is returned in the upload response.
# Phase 8: Chunks are embedded (Phase 7) and indexed into ChromaDB.
#          indexed_chunks count is returned; list endpoint shows chunk counts.

from flask import Blueprint, jsonify, request
import os
from werkzeug.utils import secure_filename

import google.generativeai as genai
from config import config
from utils.file_utils import validate_pdf_upload
from rag.loader      import load_pdf, get_page_count        # Phase 5
from rag.chunker     import chunk_pages                     # Phase 6
from rag.embeddings  import generate_embeddings             # Phase 7
from rag.vectorstore import add_chunks, get_collection_stats, get_collection, delete_document_chunks  # Phase 8

documents_bp = Blueprint("documents", __name__)


# ── GET /api/documents ────────────────────────────────────────────────────────

@documents_bp.route("/documents", methods=["GET"])
def list_documents():
    """
    GET /api/documents

    Returns a list of all PDF files that have been uploaded to the server.
    Each document includes its filename and file size.

    Phase 5+ will add: page count, chunk count, indexed status.
    """
    try:
        upload_folder = config.UPLOAD_FOLDER

        # If the upload folder doesn't exist yet, return an empty list
        if not os.path.exists(upload_folder):
            return jsonify({"documents": [], "count": 0, "status": "success"}), 200

        # Build a list of document objects for each PDF file found
        documents = []
        for filename in os.listdir(upload_folder):
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(upload_folder, filename)
                file_size_bytes = os.path.getsize(filepath)

                # Phase 5: get page count from the saved PDF
                pages = get_page_count(filepath)

                documents.append({
                    "name":    filename,
                    "size_mb": round(file_size_bytes / (1024 * 1024), 2),
                    "pages":   pages,
                    "status":  "ready",
                })

        # Phase 8: append total indexed chunk count from ChromaDB
        try:
            stats = get_collection_stats()
            total_indexed = stats["total_chunks"]
        except Exception:
            total_indexed = None   # ChromaDB unavailable — still serve the list

        return jsonify({
            "documents":     documents,
            "count":         len(documents),
            "total_indexed": total_indexed,  # total chunks in vector store
            "status":        "success"
        }), 200

    except Exception as e:
        print(f"[ERROR] list_documents failed: {e}")
        return jsonify({
            "error":  "Failed to list documents. Please try again.",
            "status": "error"
        }), 500


# ── DELETE /api/documents/<filename> ─────────────────────────────────────────

@documents_bp.route("/documents/<path:document_name>", methods=["DELETE"])
def delete_document(document_name):
    """Delete a PDF from disk and remove its indexed chunks from ChromaDB."""
    if not document_name or document_name.strip() == "":
        return jsonify({"error": "Document name is required.", "status": "error"}), 400

    safe_name = secure_filename(document_name)
    if not safe_name or not safe_name.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files can be deleted.", "status": "error"}), 400

    file_path = os.path.join(config.UPLOAD_FOLDER, safe_name)
    if not os.path.exists(file_path):
        return jsonify({"error": f"Document '{safe_name}' was not found.", "status": "error"}), 404

    try:
        os.remove(file_path)
        deleted_chunks = delete_document_chunks(safe_name)
        return jsonify({
            "status": "success",
            "message": f"Deleted '{safe_name}'",
            "deleted_chunks": deleted_chunks,
        }), 200
    except Exception as e:
        print(f"[ERROR] delete_document failed: {e}")
        return jsonify({
            "error": "Failed to delete the document. Please try again.",
            "status": "error"
        }), 500


# ── POST /api/documents/upload ────────────────────────────────────────────────

@documents_bp.route("/documents/upload", methods=["POST"])
def upload_document():
    """
    POST /api/documents/upload

    Accepts a multipart/form-data request containing a PDF file.

    Request:
        Content-Type: multipart/form-data
        Body field:   "file" → the PDF file

    Success Response (200):
        {
            "status":   "success",
            "message":  "Document uploaded successfully.",
            "document": {
                "name":     "report.pdf",
                "size_mb":  1.2,
                "path":     "documents/report.pdf"   (relative, never absolute)
            }
        }

    Error Response (400):
        {
            "status":  "error",
            "error":   "human-readable error message"
        }
    """

    # ── Step 1: Check the file field exists in the request ───────────────────
    if "file" not in request.files:
        return jsonify({
            "error":  "No file field found in the request. Please send the file as form-data with the key 'file'.",
            "status": "error"
        }), 400

    uploaded_file = request.files["file"]

    # ── Step 2: Validate the file (extension, magic bytes, size) ─────────────
    validation = validate_pdf_upload(uploaded_file, config.MAX_UPLOAD_SIZE_BYTES)

    if not validation["valid"]:
        return jsonify({
            "error":  validation["error"],
            "status": "error"
        }), 400

    # ── Step 3: Sanitize the filename ─────────────────────────────────────────
    # werkzeug.utils.secure_filename removes dangerous characters from filenames.
    # Example: "../../evil.pdf" becomes "evil.pdf"
    safe_name = secure_filename(uploaded_file.filename)

    if not safe_name:
        return jsonify({
            "error":  "Could not determine a safe filename. Please rename the file and try again.",
            "status": "error"
        }), 400

    # ── Step 4: Make sure the upload folder exists ────────────────────────────
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

    # ── Step 5: Save the file to disk ─────────────────────────────────────────
    save_path = os.path.join(config.UPLOAD_FOLDER, safe_name)

    try:
        uploaded_file.save(save_path)
        print(f"[INFO] PDF saved: {save_path}")
    except Exception as save_error:
        print(f"[ERROR] Failed to save file: {save_error}")
        return jsonify({
            "error":  "Failed to save the file on the server. Please try again.",
            "status": "error"
        }), 500

    # ── Step 6: Get file size after saving ────────────────────────────────────
    file_size_bytes = os.path.getsize(save_path)
    file_size_mb    = round(file_size_bytes / (1024 * 1024), 2)

    # ── Step 7 (Phase 5): Extract text from the PDF ───────────────────────────
    # We extract text immediately after saving so we know the page count.
    # Phase 8 will pass the chunks produced here to ChromaDB.
    pages_data         = []
    pages_extracted    = 0
    page_count         = 0
    extraction_warning = None

    try:
        pages_data      = load_pdf(save_path, safe_name)
        pages_extracted = len(pages_data)
        page_count      = get_page_count(save_path)
        print(f"[INFO] Extracted {pages_extracted} pages from '{safe_name}'.")

    except ValueError as ve:
        # The PDF opened but text extraction failed (e.g., encrypted, scanned image)
        extraction_warning = str(ve)
        print(f"[WARN] Text extraction warning for '{safe_name}': {ve}")

    except Exception as ex:
        # Non-fatal: file was uploaded successfully, extraction had an issue
        extraction_warning = f"Text extraction encountered an error: {ex}"
        print(f"[WARN] Extraction error for '{safe_name}': {ex}")

    # ── Step 8 (Phase 6): Chunk the extracted pages ───────────────────────────────
    # Splits each page's text into overlapping windows ready for embedding.
    chunks      = []
    chunk_count = 0

    if pages_data:
        try:
            chunks      = chunk_pages(pages_data, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
            chunk_count = len(chunks)
            print(f"[INFO] Chunked '{safe_name}': {chunk_count} chunks created.")

        except Exception as chunk_err:
            # Non-fatal: chunking failure should not block a successful upload
            print(f"[WARN] Chunking failed for '{safe_name}': {chunk_err}")

    # ── Step 9 (Phase 8): Embed + index chunks into ChromaDB ──────────────────────
    # Generate a 768-D vector for every chunk (Phase 7) then upsert them all
    # into ChromaDB (Phase 8). Upsert is idempotent — re-uploading the same
    # PDF replaces its chunks instead of creating duplicates.
    indexed_chunks   = 0
    indexing_warning = None

    if chunks:
        try:
            print(f"[INFO] Generating embeddings for {chunk_count} chunks...")
            embeddings = generate_embeddings([c["text"] for c in chunks])
            indexed_chunks = add_chunks(chunks, embeddings)
            print(f"[INFO] ChromaDB indexing complete: {indexed_chunks} chunks indexed.")

        except Exception as idx_err:
            # Non-fatal: the file is saved and chunked even if indexing fails.
            # The user can retry by re-uploading the document.
            indexing_warning = f"Indexing into ChromaDB failed: {idx_err}"
            print(f"[WARN] Indexing error for '{safe_name}': {idx_err}")

    # ── Step 10: Return success response ──────────────────────────────────────────────
    # SECURITY: Never return save_path (absolute server path).
    response_data = {
        "status":  "success",
        "message": f"'{safe_name}' uploaded, extracted, chunked, and indexed successfully.",
        "document": {
            "name":           safe_name,
            "size_mb":        file_size_mb,
            "path":           f"documents/{safe_name}",  # relative only
            "pages":          page_count,       # total pages in PDF
            "pages_extracted":pages_extracted,  # non-empty pages with text
            "chunks":         chunk_count,       # chunks created by chunker
            "indexed_chunks": indexed_chunks,    # chunks stored in ChromaDB
            "status":         "indexed" if indexed_chunks > 0 else "ready",
        }
    }

    # Surface any warnings so the frontend can inform the user
    warnings = []
    if extraction_warning:
        warnings.append(extraction_warning)
    if indexing_warning:
        warnings.append(indexing_warning)
    if warnings:
        response_data["warning"] = " | ".join(warnings)

    return jsonify(response_data), 200


# ── POST /api/documents/{id}/summary ─────────────────────────────────────────

@documents_bp.route("/documents/<document_id>/summary", methods=["POST"])
def summarize_document(document_id):
    """
    POST /api/documents/{document_id}/summary

    Generate a structured summary of the specified document using Gemini.
    Reads the document's chunks from ChromaDB and passes them as context.

    Phase 14 full implementation.
    """
    if not document_id or document_id.strip() == "":
        return jsonify({"error": "Document ID is required.", "status": "error"}), 400

    try:
        # ── Step 1: Retrieve all chunks for this document from ChromaDB ───────
        collection = get_collection()

        results = collection.get(
            where={"source": document_id},
            include=["documents", "metadatas"],
        )

        if not results or not results.get("documents"):
            return jsonify({
                "error": f"No indexed content found for '{document_id}'. "
                         "Please upload and process the document first.",
                "status": "error"
            }), 404

        # ── Step 2: Build context from chunks (cap at ~8000 chars to stay in context) ──
        chunks_text = results["documents"]
        context_parts = []
        total_chars = 0
        max_chars = 8000

        for i, text in enumerate(chunks_text):
            if total_chars + len(text) > max_chars:
                break
            context_parts.append(text)
            total_chars += len(text)

        context_block = "\n\n---\n\n".join(context_parts)

        # ── Step 3: Build summarization prompt ───────────────────────────────
        prompt = f"""You are DocuMind AI, an expert document analyst.

Please provide a comprehensive summary of the following document: "{document_id}"

DOCUMENT CONTENT:
{context_block}

---
Provide your response in this EXACT format:

SUMMARY:
[Write a clear, concise 3-5 sentence summary of the entire document]

KEY POINTS:
- [Key point 1]
- [Key point 2]
- [Key point 3]
- [Key point 4]
- [Key point 5]

MAIN TOPICS:
[List the 3-5 main topics or sections covered in the document]"""

        # ── Step 4: Call Groq or Gemini ──────────────────────────────────────
        if config.GROQ_API_KEY:
            from groq import Groq
            client = Groq(api_key=config.GROQ_API_KEY)
            summary_text = ""
            last_error = None
            for model_name in [
                "openai/gpt-oss-20b",
                "qwen/qwen3.8-27b",
                "qwen/qwen3.6-27b",
            ]:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1024,
                        temperature=0.2,
                    )
                    summary_text = response.choices[0].message.content.strip()
                    break
                except Exception as exc:
                    last_error = exc
                    print(f"[SUMMARY] Groq model '{model_name}' failed: {exc}")

            if not summary_text and config.GEMINI_API_KEY:
                print("[SUMMARY] Groq unavailable; falling back to Gemini.")
                import google.generativeai as genai
                genai.configure(api_key=config.GEMINI_API_KEY)
                model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
                response = model.generate_content(prompt)
                summary_text = response.text.strip() if response.text else ""

            if not summary_text:
                raise RuntimeError(
                    f"All summary models failed. Last error: {last_error}"
                ) from last_error
        else:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
            response = model.generate_content(prompt)
            summary_text = response.text.strip() if response.text else ""

        if not summary_text:
            return jsonify({
                "error": "Gemini returned an empty response. Please try again.",
                "status": "error"
            }), 500

        # ── Step 5: Parse the structured response ──────────────────────────
        summary = ""
        key_points = []
        main_topics = ""

        lines = summary_text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith("SUMMARY:"):
                current_section = "summary"
            elif line.startswith("KEY POINTS:"):
                current_section = "key_points"
            elif line.startswith("MAIN TOPICS:"):
                current_section = "main_topics"
            elif current_section == "summary" and line:
                summary += line + " "
            elif current_section == "key_points" and line.startswith("-"):
                key_points.append(line[1:].strip())
            elif current_section == "main_topics" and line:
                main_topics += line + " "

        summary = summary.strip() or summary_text

        return jsonify({
            "status":      "success",
            "document":    document_id,
            "summary":     summary,
            "key_points":  key_points,
            "main_topics": main_topics.strip(),
            "chunks_used": len(context_parts),
        }), 200

    except Exception as e:
        print(f"[ERROR] summarize_document failed for '{document_id}': {e}")
        return jsonify({
            "error":  f"Failed to summarize document: {str(e)}",
            "status": "error"
        }), 500
