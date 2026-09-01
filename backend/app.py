# app.py – Main Flask application entry point
# DocuMind AI Backend
#
# Phase 2 additions:
# - Config validation on startup (refuses to start if API key missing)
# - Global JSON error handlers (404, 405, 500 always return JSON, never HTML)
# - Request size limit enforced
# - Structured startup log

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load .env file before anything else
load_dotenv()

# Import centralized config — reads and validates all env vars
from config import config

# Create the Flask application instance
app = Flask(__name__)

# ── Request size limit ────────────────────────────────────────────────────────
# Reject uploads larger than MAX_UPLOAD_SIZE_BYTES (default 16 MB)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE_BYTES

# ── CORS Configuration ────────────────────────────────────────────────────────
# Allow the React dev server (port 5173) and any other origin in development.
# In production, replace "*" with your actual domain.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Register Route Blueprints ─────────────────────────────────────────────────
# Each blueprint handles a group of related endpoints.
# The url_prefix means all routes inside get /api/ prepended.
from routes.health import health_bp
from routes.documents import documents_bp
from routes.chat import chat_bp

app.register_blueprint(health_bp,    url_prefix="/api")
app.register_blueprint(documents_bp, url_prefix="/api")
app.register_blueprint(chat_bp,      url_prefix="/api")


# ── Global Error Handlers ─────────────────────────────────────────────────────
# Without these, Flask returns HTML error pages.
# React cannot parse HTML — it needs JSON for every response.

@app.errorhandler(400)
def bad_request(error):
    """Handle malformed requests."""
    return jsonify({
        "error": "Bad request — check your request format",
        "status": "error",
        "code": 400
    }), 400


@app.errorhandler(404)
def not_found(error):
    """Handle requests to non-existent endpoints."""
    return jsonify({
        "error": "Endpoint not found — check the API URL",
        "status": "error",
        "code": 404
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle wrong HTTP method (e.g., GET instead of POST)."""
    return jsonify({
        "error": "HTTP method not allowed for this endpoint",
        "status": "error",
        "code": 405
    }), 405


@app.errorhandler(413)
def request_too_large(error):
    """Handle file uploads that exceed MAX_CONTENT_LENGTH."""
    return jsonify({
        "error": f"File too large. Maximum allowed size is {config.MAX_UPLOAD_SIZE_MB:.0f} MB.",
        "status": "error",
        "code": 413
    }), 413


@app.errorhandler(500)
def internal_error(error):
    """
    Handle unexpected server errors.
    IMPORTANT: Never expose raw Python stack traces to the frontend.
    Log the real error server-side, return a safe message to the client.
    """
    # In production, log this to a logging service
    print(f"[ERROR] Internal server error: {error}")
    return jsonify({
        "error": "An internal server error occurred. Please try again.",
        "status": "error",
        "code": 500
    }), 500


# ── Main Entry Point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  DocuMind AI — Backend Server")
    print("="*60)

    # Validate config before starting — fail fast with clear error message
    try:
        config.validate()
    except ValueError as e:
        print(e)
        exit(1)

    # Print startup summary (no secrets shown)
    cfg = config.summary()
    print(f"  Environment  : {cfg['flask_env']}")
    print(f"  Port         : {cfg['flask_port']}")
    print(f"  Max Upload   : {cfg['max_upload_mb']:.0f} MB")
    print(f"  Gemini API   : {'[OK] Configured' if cfg['gemini_configured'] else '[!!] MISSING'}")
    print(f"  Top-K chunks : {cfg['top_k_results']}")
    print("="*60)
    print(f"\n>> Server starting at http://localhost:{cfg['flask_port']}")
    print("   Press Ctrl+C to stop\n")

    app.run(
        debug=config.DEBUG,
        host="0.0.0.0",
        port=config.FLASK_PORT
    )
