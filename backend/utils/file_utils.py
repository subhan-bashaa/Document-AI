# utils/file_utils.py – PDF file validation utilities
#
# WHY THIS FILE EXISTS:
# We need to validate every uploaded file BEFORE saving it to disk.
# Centralizing validation here keeps route code clean and makes
# it easy to add more rules in the future.

import os


# ── Constants ─────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"pdf"}

# Every valid PDF file starts with these bytes: "%PDF"
PDF_MAGIC_BYTES = b"%PDF"

# Maximum file name length (to prevent path traversal or file system issues)
MAX_FILENAME_LENGTH = 200


# ── Validation Functions ───────────────────────────────────────────────────────

def has_allowed_extension(filename: str) -> bool:
    """
    Check that the filename ends with .pdf (case-insensitive).
    This is the first quick check — before reading any file bytes.

    Example:
        has_allowed_extension("report.pdf")  -> True
        has_allowed_extension("image.png")   -> False
        has_allowed_extension("tricky")      -> False
    """
    if not filename or "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def is_valid_pdf_magic(file_storage) -> bool:
    """
    Read the first 4 bytes of the uploaded file to confirm it starts with %PDF.

    WHY: A user could rename a .jpg to .pdf and try to upload it.
    Checking the magic bytes catches this kind of trick.

    Args:
        file_storage: A Flask FileStorage object (from request.files).

    Returns:
        True if the file starts with PDF magic bytes, False otherwise.
    """
    # Read the first 4 bytes
    header = file_storage.stream.read(4)

    # IMPORTANT: Reset the stream back to position 0
    # Otherwise when we save the file, the first 4 bytes will be missing!
    file_storage.stream.seek(0)

    return header == PDF_MAGIC_BYTES


def is_filename_safe(filename: str) -> bool:
    """
    Make sure the filename does not contain path traversal characters.
    We never want a filename like "../../etc/passwd".

    Args:
        filename: The original filename from the upload.

    Returns:
        True if the filename is safe to use, False otherwise.
    """
    if not filename:
        return False

    # Reject filenames that are too long
    if len(filename) > MAX_FILENAME_LENGTH:
        return False

    # Reject path separators and other dangerous characters
    dangerous_chars = ["/", "\\", "..", "<", ">", ":", '"', "|", "?", "*"]
    for char in dangerous_chars:
        if char in filename:
            return False

    return True


def validate_pdf_upload(file_storage, max_size_bytes: int) -> dict:
    """
    Run ALL validation checks on an uploaded PDF file.

    This is the main function to call from the route.
    Returns a dict with:
        {
            "valid": True/False,
            "error": "human-readable error message or None"
        }

    Args:
        file_storage: Flask FileStorage object (from request.files["file"])
        max_size_bytes: Maximum allowed file size in bytes (from config)

    Example usage in a route:
        result = validate_pdf_upload(request.files["file"], config.MAX_UPLOAD_SIZE_BYTES)
        if not result["valid"]:
            return jsonify({"error": result["error"]}), 400
    """

    # ── Check 1: File was actually provided ──────────────────────────────────
    if file_storage is None:
        return {"valid": False, "error": "No file was provided. Please select a PDF to upload."}

    filename = file_storage.filename

    if not filename or filename.strip() == "":
        return {"valid": False, "error": "File has no name. Please select a valid PDF file."}

    # ── Check 2: Extension check ─────────────────────────────────────────────
    if not has_allowed_extension(filename):
        return {
            "valid": False,
            "error": f"Invalid file type. Only PDF files are accepted. Got: '{filename}'"
        }

    # ── Check 3: Filename safety ─────────────────────────────────────────────
    if not is_filename_safe(filename):
        return {
            "valid": False,
            "error": "Filename contains invalid characters. Please rename the file and try again."
        }

    # ── Check 4: PDF magic bytes (real content check) ────────────────────────
    if not is_valid_pdf_magic(file_storage):
        return {
            "valid": False,
            "error": "The uploaded file does not appear to be a valid PDF. Please check the file and try again."
        }

    # ── Check 5: File size ───────────────────────────────────────────────────
    # Seek to end to get file size, then reset
    file_storage.stream.seek(0, 2)   # Seek to end (os.SEEK_END = 2)
    file_size = file_storage.stream.tell()
    file_storage.stream.seek(0)      # Reset to beginning

    if file_size == 0:
        return {"valid": False, "error": "The uploaded PDF file is empty (0 bytes)."}

    if file_size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        return {
            "valid": False,
            "error": f"File too large ({actual_mb:.1f} MB). Maximum allowed size is {max_mb:.0f} MB."
        }

    # ── All checks passed ────────────────────────────────────────────────────
    return {"valid": True, "error": None}
