import math
import os
from typing import Any

from django.conf import settings
from django.utils import timezone

from .models import DocumentChunk, KnowledgeDocument


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_text(text: str) -> list[float]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            embedding = GoogleGenerativeAIEmbeddings(model="text-embedding-004", api_key=api_key)
            return embedding.embed_query(text)
        except Exception:
            pass
    return []


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks or [text]


def index_document(document: KnowledgeDocument, content: str):
    chunks = chunk_text(content)
    DocumentChunk.objects.filter(document=document).delete()
    for index, chunk in enumerate(chunks):
        vector = embed_text(chunk)
        DocumentChunk.objects.create(document=document, chunk_index=index, content=chunk, metadata={"source_name": document.title}, embedding=vector)
    document.status = "indexed"
    document.indexed_at = timezone.now()
    document.save(update_fields=["status", "indexed_at"])


def search_user_runbooks(user, query: str, limit: int = 5):
    # Keyword retrieval provides an honest fallback for legacy placeholder vectors.
    import re
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    query_vector = embed_text(query)
    results = []
    seen = set()
    for chunk in DocumentChunk.objects.select_related("document").filter(document__user=user):
        if chunk.content in seen:
            continue
        seen.add(chunk.content)
        stored = chunk.embedding or []
        semantic = len(query_vector) > 8 and len(query_vector) == len(stored)
        words = set(re.findall(r"[a-z0-9]+", chunk.content.lower()))
        score = cosine_similarity(query_vector, stored) if semantic else len(tokens & words) / max(len(tokens), 1)
        if score > 0.05:
            results.append({"document": chunk.document.title, "document_id": chunk.document_id,
                            "chunk_id": chunk.id, "method": "semantic" if semantic else "keyword",
                            "score": round(score, 4), "content": chunk.content})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]
