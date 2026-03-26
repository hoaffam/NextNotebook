"""
Retrieval evaluation for 3 modes:
  - bm25_only
  - vector_only
  - hybrid_prod (calls GraphNodes.retrieve exactly)

Computes: Recall@1/5/10/20, MRR@10, nDCG@10
Writes:
  - eval/results/retrieval_<mode>.jsonl (per-query debug)
  - eval/results/retrieval_summary.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Dict, List, Set, Tuple

from eval._common import ensure_backend_on_path, load_json
from eval.metrics import chunk_key, recall_at_k, mrr_at_k, ndcg_at_k, mean, ChunkKey


def _relevant_set(qrels_item: Dict) -> Set[ChunkKey]:
    rel = set()
    for r in qrels_item.get("relevant_chunks") or []:
        rel.add((str(r.get("document_id", "")), int(r.get("chunk_index", 0))))
    return rel


async def _retrieve_bm25_only(query: str, notebook_id: str, top_k: int) -> List[Dict]:
    from app.database.milvus_client import MilvusService
    from app.services.shared.lexical_service import LexicalBM25Service

    milvus = MilvusService()
    lexical = LexicalBM25Service(milvus)
    docs = await lexical.search(query, notebook_id, top_k=top_k)

    # Add normalized bm25 score for debug
    bm_scores = [d.get("score_bm25", 0) or 0 for d in docs]
    bm_top = max(bm_scores) if bm_scores else 0.0
    for d in docs:
        bm = d.get("score_bm25", 0) or 0
        d["_source"] = "lexical"
        d["score_bm25_norm"] = (bm / (bm_top + 1e-6)) if bm_top > 0 else 0.0
        d["score_emb_norm"] = 0.0
        d["score_combined"] = d["score_bm25_norm"]
    return docs


async def _retrieve_vector_only(query: str, notebook_id: str, top_k: int) -> List[Dict]:
    from app.database.milvus_client import MilvusService
    from app.services.shared.embedding_service import EmbeddingService

    milvus = MilvusService()
    embedding = EmbeddingService()
    qvec = await embedding.embed_query(query)
    docs = await milvus.search(query_embedding=qvec, notebook_id=notebook_id, top_k=top_k)

    emb_scores = [d.get("score", 0) or 0 for d in docs]
    emb_top = max(emb_scores) if emb_scores else 0.0
    for d in docs:
        emb = d.get("score", 0) or 0
        d["_source"] = "vector"
        d["score_bm25_norm"] = 0.0
        d["score_emb_norm"] = (emb / (emb_top + 1e-6)) if emb_top > 0 else 0.0
        d["score_combined"] = d["score_emb_norm"]
    return docs


async def _retrieve_hybrid_prod(query: str, notebook_id: str, top_k: int) -> List[Dict]:
    """
    Use EXACT production retrieve() logic.
    Note: GraphNodes.retrieve currently returns top_k=20 internally; we slice to desired k for eval.
    """
    from app.database.milvus_client import MilvusService
    from app.services.shared.embedding_service import EmbeddingService
    from app.services.shared.lexical_service import LexicalBM25Service
    from app.services.rag.nodes import GraphNodes

    milvus = MilvusService()
    embedding = EmbeddingService()
    lexical = LexicalBM25Service(milvus)
    nodes = GraphNodes(milvus_service=milvus, embedding_service=embedding, llm_service=None, web_search_service=None, lexical_service=lexical)

    state = {"question": query, "notebook_id": notebook_id, "retrieval_count": 0}
    out = await nodes.retrieve(state)
    docs = out.get("documents", [])
    return docs[:top_k]


async def evaluate_mode(qrels_path: str, notebook_id: str, mode: str, top_k: int, out_jsonl: str) -> Dict:
    data = load_json(qrels_path)
    qrels = data.get("qrels", {})

    os.makedirs(os.path.dirname(out_jsonl), exist_ok=True)
    f = open(out_jsonl, "w", encoding="utf-8")

    recalls_1, recalls_5, recalls_10, recalls_20, mrrs, ndcgs = [], [], [], [], [], []

    for qid, item in qrels.items():
        query = item.get("query_text", "")
        relevant = _relevant_set(item)

        if mode == "bm25_only":
            docs = await _retrieve_bm25_only(query, notebook_id, top_k=top_k)
        elif mode == "vector_only":
            docs = await _retrieve_vector_only(query, notebook_id, top_k=top_k)
        elif mode == "hybrid_prod":
            docs = await _retrieve_hybrid_prod(query, notebook_id, top_k=top_k)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        keys = [chunk_key(d) for d in docs]

        metrics = {
            "recall@1": recall_at_k(keys, relevant, 1),
            "recall@5": recall_at_k(keys, relevant, 5),
            "recall@10": recall_at_k(keys, relevant, 10),
            "recall@20": recall_at_k(keys, relevant, 20),
            "mrr@10": mrr_at_k(keys, relevant, 10),
            "ndcg@10": ndcg_at_k(keys, relevant, 10),
        }

        recalls_1.append(metrics["recall@1"])
        recalls_5.append(metrics["recall@5"])
        recalls_10.append(metrics["recall@10"])
        recalls_20.append(metrics["recall@20"])
        mrrs.append(metrics["mrr@10"])
        ndcgs.append(metrics["ndcg@10"])

        retrieved_debug = []
        for rank, d in enumerate(docs, start=1):
            key = chunk_key(d)
            retrieved_debug.append(
                {
                    "rank": rank,
                    "document_id": key[0],
                    "chunk_index": key[1],
                    "_source": d.get("_source"),
                    "score_bm25": d.get("score_bm25"),
                    "score_bm25_norm": d.get("score_bm25_norm"),
                    "score_emb_norm": d.get("score_emb_norm"),
                    "score_combined": d.get("score_combined") or d.get("score"),
                    "filename": d.get("filename"),
                    "is_relevant": key in relevant,
                }
            )

        row = {
            "query_id": qid,
            "mode": mode,
            "query": query,
            "relevant_count": len(relevant),
            "retrieved": retrieved_debug,
            "metrics": metrics,
        }
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    f.close()

    return {
        "mode": mode,
        "avg_recall@1": mean(recalls_1),
        "avg_recall@5": mean(recalls_5),
        "avg_recall@10": mean(recalls_10),
        "avg_recall@20": mean(recalls_20),
        "avg_mrr@10": mean(mrrs),
        "avg_ndcg@10": mean(ndcgs),
    }


async def main_async():
    ensure_backend_on_path()

    p = argparse.ArgumentParser()
    p.add_argument("--qrels", default="eval/results/qrels.json", help="qrels.json path from prepare_qrels.py")
    p.add_argument("--notebook-id", default="eval_multihoprag", help="Notebook id used in Milvus ingest")
    p.add_argument("--top-k", type=int, default=20, help="Top K to retrieve")
    p.add_argument("--mode", default="all", choices=["all", "bm25_only", "vector_only", "hybrid_prod"])
    p.add_argument("--out-dir", default="eval/results")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    modes = ["bm25_only", "vector_only", "hybrid_prod"] if args.mode == "all" else [args.mode]
    summary = {
        "notebook_id": args.notebook_id,
        "qrels": args.qrels,
        "top_k": args.top_k,
        "modes": {},
    }

    for m in modes:
        out_jsonl = os.path.join(args.out_dir, f"retrieval_{m}.jsonl")
        print(f"[retrieval] running mode={m} top_k={args.top_k}")
        res = await evaluate_mode(args.qrels, args.notebook_id, m, args.top_k, out_jsonl)
        summary["modes"][m] = res

    with open(os.path.join(args.out_dir, "retrieval_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("[retrieval] summary saved to eval/results/retrieval_summary.json")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

