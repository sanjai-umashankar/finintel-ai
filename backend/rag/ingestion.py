"""
Document ingestion pipeline: file bytes -> text -> chunks -> vector store.

    PDF/document -> Text extraction -> Chunking -> Embedding -> Vector store
"""
from typing import List
from .embeddings import SimpleVectorStore

CHUNK_SIZE = 600       # characters per chunk
CHUNK_OVERLAP = 80

# Single shared in-memory store for the process. Swap for a persistent
# ChromaDB client if you want documents to survive a server restart.
store = SimpleVectorStore()


def extract_text(filename: str, raw_bytes: bytes) -> str:
    """Extract plain text from an uploaded file. Supports .txt natively;
    supports .pdf if PyPDF2/pypdf is installed, otherwise degrades
    gracefully with a clear message instead of crashing."""
    lower = filename.lower()

    if lower.endswith(".txt") or lower.endswith(".md"):
        return raw_bytes.decode("utf-8", errors="ignore")

    if lower.endswith(".pdf"):
        try:
            from pypdf import PdfReader  # optional dependency
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # optional dependency, older name
            except ImportError:
                return ""  # caller records this as a failed/empty extraction
        import io
        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return ""

    # Fallback: try decoding as text anyway
    return raw_bytes.decode("utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = " ".join(text.split())  # normalize whitespace
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def ingest_document(document_id: str, filename: str, symbol: str, raw_bytes: bytes) -> dict:
    """Full pipeline for one uploaded document. Returns ingestion status."""
    text = extract_text(filename, raw_bytes)
    if not text.strip():
        return {"status": "failed", "chunks": 0, "reason": "Could not extract text from file."}

    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        store.add(
            chunk_id=f"{document_id}:{i}",
            text=chunk,
            metadata={"document_id": document_id, "filename": filename, "symbol": symbol.upper(), "chunk_index": i},
        )
    return {"status": "processed", "chunks": len(chunks), "reason": None}
