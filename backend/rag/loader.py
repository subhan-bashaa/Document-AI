# rag/loader.py – PDF text extraction module
#
# WHY THIS FILE EXISTS:
# PDFs are binary files — the AI cannot read them directly.
# We use PyMuPDF (imported as "fitz") to convert each PDF page
# into plain text, preserving the page number and source filename.
#
# The output of this module feeds directly into chunker.py (Phase 6).
#
# PyMuPDF docs: https://pymupdf.readthedocs.io/

import fitz  # PyMuPDF — installed as "PyMuPDF" in requirements.txt
import re


# ── Text Cleaning ─────────────────────────────────────────────────────────────

def clean_text(raw_text: str) -> str:
    """
    Clean extracted page text:
      - Replace multiple newlines with a single newline
      - Replace multiple spaces/tabs with a single space
      - Strip leading and trailing whitespace

    WHY: PDF extraction often produces excessive whitespace,
    double spaces, and stray newlines from PDF layout encoding.
    Clean text produces better embeddings and better answers.

    Args:
        raw_text: Raw text string extracted by PyMuPDF.

    Returns:
        Cleaned text string.
    """
    # Step 1: Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", raw_text)

    # Step 2: Replace tabs and runs of spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Step 3: Clean up spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    # Step 4: Strip leading/trailing whitespace from the whole block
    return text.strip()


# ── Main Extraction Function ───────────────────────────────────────────────────

def load_pdf(file_path: str, filename: str) -> list[dict]:
    """
    Extract text from a PDF file, page by page, using PyMuPDF.

    For every non-empty page, this function returns a dict:
        {
            "text":   "cleaned page text...",
            "page":   3,              ← 1-based page number (human-readable)
            "source": "report.pdf"    ← original filename
        }

    Empty pages are silently skipped.

    Args:
        file_path: Absolute path to the saved PDF file on disk.
        filename:  Original filename (e.g., "college_handbook.pdf").
                   This is stored with each page for source attribution.

    Returns:
        List of page dicts — one dict per non-empty page.
        Returns an empty list if the PDF has no extractable text.

    Raises:
        ValueError: If the file cannot be opened as a PDF.
        RuntimeError: If PyMuPDF encounters an unrecoverable error.

    Example:
        pages = load_pdf("/backend/documents/report.pdf", "report.pdf")
        # pages[0] = {"text": "Introduction...", "page": 1, "source": "report.pdf"}
    """

    pages = []  # We'll collect one dict per non-empty page here

    try:
        # Open the PDF file with PyMuPDF
        # fitz.open() can open PDFs, XPS, EPUB, and other formats
        pdf_document = fitz.open(file_path)

    except fitz.FileDataError as e:
        # The file exists but is not a valid/readable PDF
        raise ValueError(
            f"Could not open '{filename}' as a PDF. "
            f"The file may be corrupted or password-protected. Details: {e}"
        )
    except Exception as e:
        raise RuntimeError(f"Unexpected error opening PDF '{filename}': {e}")

    try:
        total_pages = len(pdf_document)
        print(f"[INFO] Extracting text from '{filename}' ({total_pages} pages)...")

        for page_index in range(total_pages):
            # Get the page object (0-indexed internally)
            page = pdf_document[page_index]

            # Extract all text from this page as a plain string.
            # "text" mode returns plain UTF-8 text.
            # "blocks" mode would give structured blocks — we use "text" for simplicity.
            raw_text = page.get_text("text")

            # Clean whitespace artifacts from the PDF encoding
            cleaned = clean_text(raw_text)

            # Skip pages with no meaningful text (e.g., image-only pages, blank pages)
            # A page is considered empty if it has fewer than 20 characters after cleaning.
            if len(cleaned) < 20:
                print(f"  [SKIP] Page {page_index + 1} — too short ({len(cleaned)} chars), skipping.")
                continue

            # Build the page dict — this is the internal representation used throughout the pipeline
            page_dict = {
                "text":   cleaned,
                "page":   page_index + 1,   # Convert from 0-index to human-readable 1-index
                "source": filename,
            }

            pages.append(page_dict)

            print(f"  [OK]   Page {page_index + 1} — {len(cleaned)} characters extracted.")

    finally:
        # Always close the PDF document to release file handles
        pdf_document.close()

    print(f"[INFO] Extraction complete: {len(pages)} pages extracted from '{filename}'.")
    return pages


# ── Helper: Get page count without full extraction ────────────────────────────

def get_page_count(file_path: str) -> int:
    """
    Quickly return the total number of pages in a PDF.
    Used when we only need the page count (e.g., for metadata display).

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Integer page count, or 0 if the file cannot be opened.
    """
    try:
        doc = fitz.open(file_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0
