"""
reindex.py — Re-index all uploaded PDFs into ChromaDB using local embeddings.
No API keys or quota needed — uses ChromaDB's built-in ONNX model.
"""
import os, glob
from rag.loader import load_pdf
from rag.chunker import chunk_pages
from rag.embeddings import generate_embeddings   # now uses local ONNX model
from rag.vectorstore import add_chunks
from config import config

docs_folder = config.UPLOAD_FOLDER
pdfs = glob.glob(os.path.join(docs_folder, "*.pdf"))
print(f"Found {len(pdfs)} PDFs to index: {[os.path.basename(p) for p in pdfs]}")
print(f"Embedding mode: {config.EMBEDDING_MODEL}\n")

for pdf_path in pdfs:
    filename = os.path.basename(pdf_path)
    print(f"Indexing: {filename}")

    pages = load_pdf(pdf_path, filename)
    print(f"  Pages extracted: {len(pages)}")

    chunks = chunk_pages(pages, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    print(f"  Chunks created:  {len(chunks)}")

    texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(texts)
    print(f"  Embeddings done: {len(embeddings)} vectors (dim={len(embeddings[0])})")

    added = add_chunks(chunks, embeddings)
    print(f"  Indexed in ChromaDB: {added} chunks\n")

print("All done! Re-indexing complete.")
