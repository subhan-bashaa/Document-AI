# DocuMind AI 🧠

> Intelligent Document Research Assistant using Retrieval-Augmented Generation (RAG)

## What is DocuMind AI?

DocuMind AI is a Generative AI internship project that demonstrates:

- **RAG (Retrieval-Augmented Generation)** — Ground AI answers in real documents
- **Google Gemini** — State-of-the-art LLM for answer generation
- **ChromaDB** — Local vector database for semantic search
- **Embeddings** — Convert text to mathematical vectors for similarity matching
- **Responsible AI** — Only answers from uploaded documents, never hallucinates

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Frontend   | React + Vite            |
| Backend    | Python + Flask          |
| LLM        | Google Gemini API       |
| Embeddings | Google Generative AI    |
| Vector DB  | ChromaDB                |
| PDF        | PyMuPDF                 |

## Project Structure

```
documind-ai/
├── frontend/          # React + Vite application
│   └── src/
│       ├── components/   # Reusable UI components
│       ├── pages/        # Full page views
│       └── services/     # API communication layer
│
├── backend/           # Python Flask REST API
│   ├── routes/           # API endpoints
│   ├── rag/              # RAG pipeline modules
│   │   ├── loader.py     # PDF text extraction
│   │   ├── chunker.py    # Text chunking
│   │   ├── embeddings.py # Vector embedding
│   │   ├── retriever.py  # Semantic search
│   │   └── generator.py  # Gemini answer generation
│   ├── vectorstore/      # ChromaDB data
│   └── documents/        # Uploaded PDF storage
│
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
# Edit .env and replace: GEMINI_API_KEY=your_gemini_api_key_here

# Start Flask server
python app.py
```

Backend runs at: http://localhost:5000

### Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start React development server
npm run dev
```

Frontend runs at: http://localhost:5173

### Verify Connection

1. Open http://localhost:5173
2. The status indicator should show **"Backend Online"**
3. This confirms frontend ↔ backend communication works ✅

## API Endpoints

| Method | Endpoint                        | Description              | Phase |
|--------|---------------------------------|--------------------------|-------|
| GET    | /api/health                     | Server health check      | 1     |
| GET    | /api/documents                  | List uploaded documents  | 4     |
| POST   | /api/documents/upload           | Upload a PDF             | 4     |
| POST   | /api/chat                       | Ask a question (RAG)     | 10    |
| POST   | /api/documents/{id}/summary     | Summarize a document     | 14    |

## Development Phases

| Phase | Feature                  | Status      |
|-------|--------------------------|-------------|
| 1     | Project Setup            | ✅ Complete |
| 2     | Flask Backend            | ✅ Complete |
| 3     | React Frontend           | ✅ Complete |
| 4     | PDF Upload               | ✅ Complete |
| 5     | Text Extraction          | ✅ Complete |
| 6     | Chunking                 | ✅ Complete |
| 7     | Embeddings               | ✅ Complete |
| 8     | ChromaDB                 | ✅ Complete |
| 9     | Semantic Retrieval       | 🔲 Pending  |
| 10    | Gemini Integration       | 🔲 Pending  |
| 11    | RAG Prompt               | 🔲 Pending  |
| 12    | Chat UI                  | 🔲 Pending  |
| 13    | Source Display           | 🔲 Pending  |
| 14    | Document Summarization   | 🔲 Pending  |

## Security Notes

- API keys are stored in `.env` files (never committed to Git)
- `.gitignore` excludes all `.env` files
- File uploads are validated (type and size)
- Gemini API only called from backend (never exposed to frontend)

## License

This project is built for educational purposes as part of a Generative AI internship.
