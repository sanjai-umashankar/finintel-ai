"""
Retrieval step of the RAG pipeline. Used by the Fundamental Agent.

Order of preference:
 1. Real chunks from documents the user uploaded for this symbol.
 2. Demo/sample document chunks (clearly labelled as such).
 3. Nothing available -> Fundamental Agent must say so and lower confidence.
"""
from typing import List, Dict
from .ingestion import store
from backend.data.demo_data import DOCUMENTS

DEFAULT_QUERY = "revenue growth profit earnings debt cash flow management outlook business performance"


def retrieve_for_symbol(symbol: str, query: str = DEFAULT_QUERY, top_k: int = 3) -> Dict:
    symbol = symbol.upper()

    if store.has_any({"symbol": symbol}):
        results = store.query(query, filter_metadata={"symbol": symbol}, top_k=top_k)
        return {"available": True, "is_demo": False, "chunks": results}

    demo = DOCUMENTS.get(symbol)
    if demo:
        chunks = [
            {
                "document_id": "demo",
                "filename": demo["filename"] + " (DEMO)",
                "symbol": symbol,
                "chunk_index": i,
                "text": text,
                "score": None,
            }
            for i, text in enumerate(demo["chunks"][:top_k])
        ]
        return {"available": True, "is_demo": True, "chunks": chunks}

    return {"available": False, "is_demo": False, "chunks": []}
