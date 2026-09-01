// services/api.js — DocuMind AI API Service
//
// This file is the ONLY place in the frontend that knows about the backend URL.
// All API calls go through this file, never directly inside components.
// This makes it easy to change the backend URL in one place.

// The backend URL is read from the Vite environment variable.
// In development this is: http://localhost:5000
// In production this would change to the deployed server URL.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

/**
 * Generic fetch wrapper with error handling.
 * All API functions use this instead of calling fetch() directly.
 *
 * @param {string} endpoint - The API endpoint (e.g., "/health")
 * @param {object} options  - Standard fetch() options
 * @returns {Promise<any>}  - Parsed JSON response
 * @throws {Error}          - With a user-friendly message on failure
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    // Try to parse JSON regardless of status code
    // The backend always returns JSON (even for errors)
    const data = await response.json();

    if (!response.ok) {
      // Use the backend's error message if available
      const errorMessage = data?.error || `Server error: ${response.status}`;
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    // If it's already our custom error, re-throw it
    if (error instanceof Error && error.message !== "Failed to fetch") {
      throw error;
    }
    // Network error (backend not running, CORS issue, etc.)
    throw new Error(
      "Cannot connect to DocuMind AI backend. " +
      "Please make sure the Flask server is running on port 5000."
    );
  }
}

// ─── API Functions ──────────────────────────────────────────────────────────

/**
 * Check if the backend server is alive and running.
 * Called on app startup to show backend connection status.
 *
 * @returns {Promise<{status, message, timestamp, version}>}
 */
export async function checkHealth() {
  return apiFetch("/health");
}

/**
 * Upload a PDF document to the backend for processing.
 * Uses multipart/form-data (not JSON) because we're sending a file.
 *
 * Phase 4 implementation.
 *
 * @param {File} file - The PDF File object from the browser
 * @returns {Promise<{document_id, filename, pages, chunks}>}
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  // Note: Do NOT set Content-Type header for FormData
  // The browser sets it automatically with the correct boundary
  return apiFetch("/documents/upload", {
    method: "POST",
    headers: {}, // Override the default JSON Content-Type
    body: formData,
  });
}

/**
 * Get the list of all uploaded and indexed documents.
 *
 * @returns {Promise<{documents: Array}>}
 */
export async function getDocuments() {
  return apiFetch("/documents");
}

/**
 * Delete a PDF from disk and remove its indexed chunks from ChromaDB.
 *
 * @param {string} documentName - The uploaded PDF filename
 * @returns {Promise<{status, message, deleted}>}
 */
export async function deleteDocument(documentName) {
  return apiFetch(`/documents/${encodeURIComponent(documentName)}`, {
    method: "DELETE",
  });
}

/**
 * Send a user question to the RAG pipeline.
 * The backend will retrieve relevant chunks and ask Gemini.
 *
 * Phase 9–11 implementation.
 *
 * @param {string} question - The user's question
 * @returns {Promise<{answer: string, sources: Array}>}
 */
export async function askQuestion(question) {
  return apiFetch("/chat", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

/**
 * Request a summary for a specific document.
 *
 * Phase 14 implementation.
 *
 * @param {string} documentId - The document's unique ID
 * @returns {Promise<{summary: string, key_points: Array}>}
 */
export async function summarizeDocument(documentId) {
  return apiFetch(`/documents/${documentId}/summary`, {
    method: "POST",
  });
}
