"""
MentorOS – Vector Store (FAISS + Sentence Transformers)
Semantic memory for notes.
"""
import os
import asyncio
from typing import List, Optional
from core.config import settings
import structlog

log = structlog.get_logger()

# Lazy-load heavy models
_embeddings = None
_vector_store = None
_store_lock = asyncio.Lock()


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            _embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
            log.info("embeddings.loaded", model=settings.EMBEDDING_MODEL)
        except Exception as e:
            log.warning("embeddings.unavailable", error=str(e))
    return _embeddings


def _get_or_create_store():
    global _vector_store
    embeddings = _get_embeddings()
    if embeddings is None:
        return None

    try:
        from langchain_community.vectorstores import FAISS
        path = settings.VECTOR_STORE_PATH
        index_path = os.path.join(path, "index.faiss")

        if os.path.exists(index_path):
            _vector_store = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
        else:
            os.makedirs(path, exist_ok=True)
            _vector_store = FAISS.from_texts(["MentorOS semantic memory initialized"], embeddings)
            _vector_store.save_local(path)

        return _vector_store
    except Exception as e:
        log.warning("vectorstore.unavailable", error=str(e))
        return None


async def add_to_vector_store(text: str, metadata: dict = None) -> bool:
    """Add text to FAISS vector store (runs in thread pool to avoid blocking)."""
    async with _store_lock:
        try:
            def _add():
                store = _get_or_create_store()
                if store is None:
                    return False
                store.add_texts([text], metadatas=[metadata or {}])
                store.save_local(settings.VECTOR_STORE_PATH)
                return True

            return await asyncio.get_event_loop().run_in_executor(None, _add)
        except Exception as e:
            log.error("vectorstore.add_error", error=str(e))
            return False


async def semantic_search(query: str, k: int = 5, user_id: Optional[int] = None) -> List[dict]:
    """Search vector store for semantically similar notes."""
    try:
        def _search():
            store = _get_or_create_store()
            if store is None:
                return []
            docs = store.similarity_search_with_score(query, k=k)
            results = []
            for doc, score in docs:
                meta = doc.metadata or {}
                if user_id and meta.get("user_id") and meta["user_id"] != user_id:
                    continue
                results.append({
                    "content": doc.page_content,
                    "score": float(score),
                    "metadata": meta
                })
            return results

        return await asyncio.get_event_loop().run_in_executor(None, _search)
    except Exception as e:
        log.error("vectorstore.search_error", error=str(e))
        return []
