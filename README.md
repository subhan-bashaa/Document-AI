# DocuMind AI 🧠

> **Responsible-first Document Research Assistant powered by RAG + Google Gemini**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.x-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35)](https://trychroma.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini_2.5_Flash-4285F4?logo=google&logoColor=white)](https://aistudio.google.com)
[![License](https://img.shields.io/badge/License-Educational-green)](#license)

---

## What is DocuMind AI?

DocuMind AI is a **full-stack AI application** that lets you upload PDF documents and ask questions about them in natural language. It uses **Retrieval-Augmented Generation (RAG)** to ensure every answer is grounded in your uploaded documents — never hallucinated from the model's training data.

Built as part of a Generative AI internship, it demonstrates a production-grade RAG pipeline from PDF ingestion to AI-generated, source-cited answers.

### Key Principles

- 🔒 **Responsible AI** — Answers come *only* from your uploaded documents
- 📄 **Source-cited** — Every answer links back to the exact PDF page it came from
- ⚡ **Fast** — Groq (Llama/Qwen) for inference, Gemini as reliable fallback
- 🧠 **Semantic Search** — ChromaDB vector database for context-aware retrieval

---

## Features

| Feature | Description |
|---------|-------------|
| 📤 **PDF Upload** | Drag & drop or browse to upload PDFs (max 16 MB) |
| 🔍 **Semantic Search** | Embedding-based retrieval from ChromaDB |
| 🤖 **AI Q&A** | Grounded answers via Groq (Llama/Qwen) or Google Gemini |
| 📑 **Source Display** | Every answer includes the source document + page number |
| 📋 **Document Summarization** | One-click AI summary of any uploaded document |
| 🗂️ **Multi-document** | Upload and query multiple PDFs simultaneously |
| 🌐 **Modern UI** | Responsive React frontend with dark theme |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite 8 | UI & user interaction |
| **Backend** | Python 3.10+ + Flask 3 | REST API server |
| **LLM (Primary)** | Groq API (Llama / Qwen) | Fast AI answer generation |
| **LLM (Fallback)** | Google Gemini 2.5 Flash | Reliable fallback LLM |
| **Embeddings** | Google Generative AI (`text-embedding-004`) | Convert text to vectors |
| **Vector DB** | ChromaDB | Semantic similarity search |
| **PDF Parsing** | PyMuPDF (fitz) | Text extraction from PDFs |
| **Styling** | Vanilla CSS | Custom dark-theme UI |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│              (Vite dev server :5173)                     │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP / REST API
┌────────────────────────▼─────────────────────────────────┐
│                   Flask Backend (:5000)                   │
│                                                          │
│  POST /api/documents/upload   POST /api/chat             │
│  GET  /api/documents          POST /api/documents/{id}/summary │
│  GET  /api/health                                        │
└──────┬────────────────────────────────────────┬──────────┘
       │                                        │
┌──────▼──────┐                      ┌──────────▼────────┐
│ RAG Pipeline│                      │   LLM APIs        │
│             │                      │                   │
│ 1. Load PDF │                      │ • Groq  (primary) │
│ 2. Chunk    │                      │ • Gemini(fallback)│
│ 3. Embed    │                      └───────────────────┘
│ 4. Store    │
│ 5. Retrieve │──► ChromaDB (local vector store)
│ 6. Generate │
└─────────────┘
```

---

## Project Structure

```
documind-ai/
│
├── README.md
├── .gitignore
│
├── backend/                    # Python Flask REST API
│   ├── app.py                  # App entry point, blueprints, error handlers
│   ├── config.py               # Centralized config (reads .env)
│   ├── reindex.py              # CLI tool: rebuild the entire vector index
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # API keys (NOT committed to Git)
│   │
│   ├── rag/                    # Core RAG pipeline
│   │   ├── loader.py           # PDF text extraction (PyMuPDF)
│   │   ├── chunker.py          # Split text into overlapping chunks
│   │   ├── embeddings.py       # Generate Google embedding vectors
│   │   ├── vectorstore.py      # ChromaDB read/write operations
│   │   ├── retriever.py        # Semantic search (Phase 9)
│   │   └── generator.py        # LLM answer generation (Phases 10 & 11)
│   │
│   ├── routes/                 # Flask route blueprints
│   │   ├── health.py           # GET  /api/health
│   │   ├── documents.py        # GET/POST /api/documents
│   │   └── chat.py             # POST /api/chat
│   │
│   ├── utils/                  # Shared utilities
│   │   ├── file_utils.py       # File validation, safe naming
│   │   └── helpers.py          # General helper functions
│   │
│   ├── documents/              # Uploaded PDFs (auto-created)
│   └── vectorstore/            # ChromaDB persistent storage
│
└── frontend/                   # React + Vite application
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx            # App entry point
        ├── App.jsx             # Root component + state management
        ├── App.css             # Global layout styles
        ├── index.css           # Design tokens & base styles
        ├── components/
        │   ├── Header.jsx      # Top navigation bar
        │   ├── Sidebar.jsx     # Document upload + list panel
        │   ├── ChatArea.jsx    # Q&A chat interface
        │   ├── EmptyState.jsx  # Welcome screen
        │   ├── LoadingDots.jsx # Animated loading indicator
        │   └── components.css  # Component-level styles
        ├── pages/              # Full page views (future routing)
        └── services/
            └── api.js          # Axios API client
```

---

## Quick Start

### Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher
- **Google Gemini API key** → [Get one free at Google AI Studio](https://aistudio.google.com/app/apikey)
- *(Optional)* **Groq API key** → [Get one free at console.groq.com](https://console.groq.com) for faster inference

---

### 1. Clone the repository

```bash
git clone https://github.com/subhan-bashaa/Document-AI.git
cd Document-AI
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Configure environment variables

Create (or edit) `backend/.env`:

```env
# Required — get a free key at https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional — enables faster Groq inference (falls back to Gemini if not set)
GROQ_API_KEY=your_groq_api_key_here

# Flask settings (defaults are fine for development)
FLASK_PORT=5000
FLASK_ENV=development
MAX_UPLOAD_SIZE_MB=16
TOP_K_RESULTS=5
```

#### Start the backend

```bash
python app.py
```

Expected output:
```
============================================================
  DocuMind AI — Backend Server
============================================================
  Environment  : development
  Port         : 5000
  Max Upload   : 16 MB
  Gemini API   : [OK] Configured
  Top-K chunks : 5
============================================================

>> Server starting at http://localhost:5000
```

---

### 3. Frontend Setup

```bash
# In a new terminal
cd frontend

# Install Node.js dependencies
npm install

# Start the Vite dev server
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

### 4. Using the App

1. Open **http://localhost:5173** in your browser
2. **Upload a PDF** — drag & drop or click "browse files" in the left panel
3. Wait for indexing to complete (document appears in the list)
4. **Ask a question** — type in the chat area and press Enter
5. Receive a **source-cited answer** grounded in your document

---

## API Reference

### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "message": "DocuMind AI backend is running"
}
```

---

### List Documents

```http
GET /api/documents
```

**Response:**
```json
{
  "documents": [
    {
      "id": "college_handbook",
      "filename": "college_handbook.pdf",
      "pages": 42,
      "uploaded_at": "2026-09-01T14:30:00Z"
    }
  ],
  "status": "success"
}
```

---

### Upload a PDF

```http
POST /api/documents/upload
Content-Type: multipart/form-data

file: <PDF file>
```

**Response:**
```json
{
  "message": "Document uploaded and indexed successfully",
  "document_id": "college_handbook",
  "chunks_indexed": 87,
  "status": "success"
}
```

**Error codes:**
- `400` — No file provided or file is not a PDF
- `413` — File exceeds 16 MB limit
- `500` — Processing / indexing failed

---

### Ask a Question (RAG Chat)

```http
POST /api/chat
Content-Type: application/json

{
  "question": "What are the eligibility requirements for scholarships?",
  "source_filter": "college_handbook.pdf"
}
```

> `source_filter` is optional — omit it to search across all uploaded documents.

**Response:**
```json
{
  "answer": "According to the college handbook, scholarship eligibility requires a minimum GPA of 3.5...",
  "sources": [
    { "document": "college_handbook.pdf", "page": 14 },
    { "document": "college_handbook.pdf", "page": 15 }
  ],
  "status": "success"
}
```

**Error codes:**
- `400` — Missing/empty question; question exceeds 2000 characters
- `503` — No documents indexed yet (upload a PDF first)
- `500` — LLM API failure

---

### Summarize a Document

```http
POST /api/documents/{document_id}/summary
```

**Response:**
```json
{
  "summary": "This document covers admission procedures, scholarship requirements, course registration...",
  "status": "success"
}
```

---

## RAG Pipeline Explained

```
PDF File
   │
   ▼
[1. LOAD]      PyMuPDF extracts raw text page by page
   │
   ▼
[2. CHUNK]     Text split into ~500-token overlapping chunks
               (overlap preserves context across chunk boundaries)
   │
   ▼
[3. EMBED]     Google text-embedding-004 converts each chunk
               into a 768-dimensional vector
   │
   ▼
[4. STORE]     Vectors + metadata saved to ChromaDB (on disk)
   │
   ▼  (on user question)
[5. RETRIEVE]  User question embedded → cosine similarity search
               → top-K most relevant chunks returned
   │
   ▼
[6. GENERATE]  RAG prompt built:
               "Answer ONLY from these document excerpts..."
               + context chunks + user question
               → sent to Groq / Gemini → grounded answer
   │
   ▼
Answer + source citations returned to frontend
```

---

## Development Phases

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Project Setup | ✅ Complete |
| 2 | Flask Backend | ✅ Complete |
| 3 | React Frontend | ✅ Complete |
| 4 | PDF Upload | ✅ Complete |
| 5 | Text Extraction | ✅ Complete |
| 6 | Chunking | ✅ Complete |
| 7 | Embeddings | ✅ Complete |
| 8 | ChromaDB Vector Store | ✅ Complete |
| 9 | Semantic Retrieval | ✅ Complete |
| 10 | Gemini / Groq Integration | ✅ Complete |
| 11 | RAG Prompt Engineering | ✅ Complete |
| 12 | Chat UI | ✅ Complete |
| 13 | Source Display | ✅ Complete |
| 14 | Document Summarization | ✅ Complete |

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | — | Google Gemini API key |
| `GROQ_API_KEY` | No | — | Groq API key (enables faster LLM inference) |
| `FLASK_PORT` | No | `5000` | Port the Flask server listens on |
| `FLASK_ENV` | No | `development` | `development` or `production` |
| `MAX_UPLOAD_SIZE_MB` | No | `16` | Maximum PDF upload size in MB |
| `TOP_K_RESULTS` | No | `5` | Number of chunks retrieved per query |

---

## Security Notes

- 🔑 API keys are stored in `.env` files — **never committed to Git**
- 🚫 `.gitignore` excludes all `.env` files and the `venv/` directory
- ✅ File uploads are validated for type (PDF only) and size
- 🔒 Gemini/Groq API is called **only from the backend** — never exposed to the browser
- 🛡️ Global error handlers always return JSON (no raw stack traces sent to client)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `GEMINI_API_KEY is not configured` | Create `backend/.env` and add your API key |
| `Failed to search documents` | Upload at least one PDF before asking questions |
| Groq API errors | App falls back to Gemini automatically; check your `GROQ_API_KEY` |
| Frontend can't reach backend | Ensure Flask is running on port 5000; check `vite.config.js` proxy |
| PDF not indexing | Ensure the PDF is text-based (not a scanned image without OCR) |

---

## Author

**Subhan Basha** — Generative AI Internship Project
GitHub: [@subhan-bashaa](https://github.com/subhan-bashaa)

---

## License

Built for educational purposes as part of a Generative AI internship.
Feel free to fork, learn, and build on it. 🚀
