"""
Minimal, dependency-free text embedding + similarity for the RAG pipeline.

This uses a bag-of-words term-frequency vector and cosine similarity
instead of a real embedding model, so the whole app runs with zero API
keys and zero extra installs.

TO UPGRADE: replace `embed()` with a call to OpenAI's embeddings endpoint
(or any sentence-transformers model) and swap `SimpleVectorStore` below
for a `chromadb.PersistentClient` collection -- `retrieval.py` is the
only file that needs to change, since it only calls `embed()` and
`SimpleVectorStore.query()`.
"""
import math
import re
from collections import Counter
from typing import List, Dict

_WORD_RE = re.compile(r"[a-zA-Z]{2,}")

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is",
    "was", "were", "are", "with", "by", "as", "at", "it", "this", "that",
    "be", "has", "have", "had", "its", "their", "from", "which", "over",
    "into", "than", "also", "will", "may", "such",
}


def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(text) if w.lower() not in _STOPWORDS]


def embed(text: str) -> Counter:
    """Return a term-frequency vector for `text`."""
    return Counter(_tokenize(text))


def cosine_similarity(vec_a: Counter, vec_b: Counter) -> float:
    if not vec_a or not vec_b:
        return 0.0
    common = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SimpleVectorStore:
    """In-memory stand-in for a ChromaDB collection: id -> (vector, metadata)."""

    def __init__(self):
        self._items: Dict[str, dict] = {}

    def add(self, chunk_id: str, text: str, metadata: dict):
        self._items[chunk_id] = {
            "vector": embed(text),
            "text": text,
            "metadata": metadata,
        }

    def query(self, query_text: str, filter_metadata: dict = None, top_k: int = 3) -> List[dict]:
        q_vec = embed(query_text)
        results = []
        for item in self._items.values():
            if filter_metadata:
                if any(item["metadata"].get(k) != v for k, v in filter_metadata.items()):
                    continue
            score = cosine_similarity(q_vec, item["vector"])
            if score > 0:
                results.append({**item["metadata"], "text": item["text"], "score": round(score, 3)})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def has_any(self, filter_metadata: dict) -> bool:
        return any(
            all(item["metadata"].get(k) == v for k, v in filter_metadata.items())
            for item in self._items.values()
        )
