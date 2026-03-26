"""
IR metrics for retrieval evaluation: Recall@K, MRR@10, nDCG@10.
All metrics are computed at chunk-level with keys (document_id, chunk_index).
"""

from __future__ import annotations

import math
from typing import Iterable, List, Set, Tuple


ChunkKey = Tuple[str, int]


def chunk_key(doc: dict) -> ChunkKey:
    return (str(doc.get("document_id", "")), int(doc.get("chunk_index", 0)))


def recall_at_k(retrieved: List[ChunkKey], relevant: Set[ChunkKey], k: int) -> float:
    if not relevant:
        return 0.0
    topk = set(retrieved[:k])
    hit = len(topk & relevant)
    return hit / len(relevant)


def mrr_at_k(retrieved: List[ChunkKey], relevant: Set[ChunkKey], k: int = 10) -> float:
    for rank, key in enumerate(retrieved[:k], start=1):
        if key in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: List[ChunkKey], relevant: Set[ChunkKey], k: int = 10) -> float:
    """
    Binary nDCG@K.
    rel_i is 1 if retrieved[i] in relevant else 0.
    """
    def dcg(keys: List[ChunkKey]) -> float:
        score = 0.0
        for i, key in enumerate(keys[:k], start=1):
            rel = 1.0 if key in relevant else 0.0
            if rel:
                score += rel / math.log2(i + 1)
        return score

    dcg_val = dcg(retrieved)
    ideal_list = [("REL", i) for i in range(min(k, len(relevant)))]  # dummy placeholders
    # Ideal DCG for binary relevance is sum_{i=1..min(k,|rel|)} 1/log2(i+1)
    idcg = 0.0
    for i in range(1, min(k, len(relevant)) + 1):
        idcg += 1.0 / math.log2(i + 1)
    return (dcg_val / idcg) if idcg > 0 else 0.0


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0

