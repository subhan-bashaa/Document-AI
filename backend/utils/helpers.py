# utils/helpers.py – Shared utility functions
# Contains reusable helper functions that multiple modules will use.

import os
import uuid


def generate_unique_id() -> str:
    """Generate a unique ID string (used for document and chunk IDs)."""
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from a filename for safe storage.
    Only allows alphanumeric characters, dots, hyphens, and underscores.
    """
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    sanitized = "".join(c if c in safe_chars else "_" for c in filename)
    return sanitized


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """
    Check if a filename has an allowed extension.
    By default, only PDF files are allowed.
    """
    if allowed_extensions is None:
        allowed_extensions = {"pdf"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def format_error_response(message: str, code: int = 400) -> tuple:
    """
    Return a consistent JSON error response.
    Every API error should use this function so errors look the same.
    """
    from flask import jsonify
    return jsonify({"error": message, "status": "error"}), code


def format_success_response(data: dict, message: str = "Success") -> tuple:
    """
    Return a consistent JSON success response.
    Every API success should use this function.
    """
    from flask import jsonify
    return jsonify({"data": data, "message": message, "status": "success"}), 200
