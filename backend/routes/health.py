# routes/health.py – Health check endpoint
#
# GET /api/health
# Used by the React frontend to verify backend connectivity on startup.
# Also useful for monitoring tools and deployment health checks.

from flask import Blueprint, jsonify
import datetime
from config import config

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    GET /api/health

    Returns:
        200 OK with server status, version, timestamp, and safe config summary.

    The frontend calls this on startup to:
    1. Confirm the backend is reachable
    2. Show the "Backend Online" status badge
    3. Display server info in the status card
    """
    cfg = config.summary()

    return jsonify({
        "status": "ok",
        "message": "DocuMind AI backend is running",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "config": {
            "gemini_configured": cfg["gemini_configured"],
            "max_upload_mb": cfg["max_upload_mb"],
            "top_k_results": cfg["top_k_results"],
            "environment": cfg["flask_env"],
        }
    }), 200
