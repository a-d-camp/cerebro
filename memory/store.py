from __future__ import annotations

import time
import uuid
import logging
from typing import List, Dict, Any

import chromadb

from memory.scoring import rerank

logger = logging.getLogger(__name__)

_client: chromadb.Client | None = None
_collection: chromadb.Collection | None = None
COLLECTION_NAME = "cerebro_memories"


def init(chroma_path: str) -> None:
    global _client, _collection
    _client = chromadb.PersistentClient(path=chroma_path)
    _collection = _client.get_or_create_collection(COLLECTION_NAME)
    logger.info("Chroma initialised at %s (collection=%s)", chroma_path, COLLECTION_NAME)


def _get_collection() -> chromadb.Collection:
    if _collection is None:
        raise RuntimeError("Memory store not initialised. Call store.init() first.")
    return _collection


def embed_and_store(
    memory_text: str,
    source_role: str,
    message_ids: List[int],
) -> str:
    collection = _get_collection()
    mem_id = f"mem_{uuid.uuid4()}"
    metadata = {
        "created_at": time.time(),
        "source_role": source_role,
        "message_ids": ",".join(str(i) for i in message_ids),
    }
    collection.add(
        ids=[mem_id],
        documents=[memory_text],
        metadatas=[metadata],
    )
    logger.debug("Stored memory id=%s text=%r", mem_id, memory_text[:80])
    return mem_id


def find_similar(memory_text: str, threshold: float = 0.25) -> Dict[str, Any] | None:
    """Return the most similar existing memory if within distance threshold, else None."""
    collection = _get_collection()
    if collection.count() == 0:
        return None
    results = collection.query(
        query_texts=[memory_text],
        n_results=1,
        include=["documents", "metadatas", "distances"],
    )
    if results["distances"][0][0] < threshold:
        return {
            "id": results["ids"][0][0],
            "document": results["documents"][0][0],
            "metadata": results["metadatas"][0][0],
        }
    return None


def update_memory(mem_id: str, new_text: str) -> None:
    """Update an existing memory's document text."""
    _get_collection().update(ids=[mem_id], documents=[new_text])
    logger.debug("Updated memory id=%s text=%r", mem_id, new_text[:80])


def get_all() -> List[str]:
    """Return all memory documents in the collection."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    result = collection.get(include=["documents"])
    return result["documents"]


def retrieve(
    query: str,
    top_k: int = 20,
    top_n: int = 5,
    half_life_days: float = 30.0,
) -> List[Dict[str, Any]]:
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []

    n_results = min(top_k, count)
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    ranked = rerank(results, top_n=top_n, half_life_days=half_life_days)
    logger.debug("Retrieved %d memories (from %d candidates)", len(ranked), n_results)
    return ranked
