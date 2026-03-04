import math
import time
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

LN2 = math.log(2)


def rerank(
    results: Dict[str, Any],
    top_n: int,
    half_life_days: float,
) -> List[Dict[str, Any]]:
    """Re-rank Chroma query results using blended semantic + recency score.

    Args:
        results: Raw Chroma query results dict (ids, documents, metadatas, distances).
        top_n: Number of top results to return.
        half_life_days: Recency half-life in days (default 30).

    Returns:
        List of dicts with keys: id, document, metadata, score.
    """
    now = time.time()
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    scored = []
    for mem_id, doc, meta, dist in zip(ids, documents, metadatas, distances):
        semantic_score = 1 - (dist / 2)
        age_days = (now - meta.get("created_at", now)) / 86400
        recency_score = math.exp(-LN2 * age_days / half_life_days)
        final_score = 0.7 * semantic_score + 0.3 * recency_score

        logger.debug(
            "mem=%s semantic=%.3f recency=%.3f final=%.3f",
            mem_id, semantic_score, recency_score, final_score,
        )
        scored.append({
            "id": mem_id,
            "document": doc,
            "metadata": meta,
            "score": final_score,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
