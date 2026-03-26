"""
Prepare qrels (query → relevant chunks) from MultiHopRAG evidence_list.

Key point: evidence_list facts are SHORT, while production chunks are ~1000 chars.
We match each evidence fact to chunk(s) by robust substring matching on normalized text.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Dict, List, Tuple

from eval._common import ensure_backend_on_path, load_json, save_json, stable_doc_id_from_url, normalize_text


def _match_fact_to_chunks(fact: str, chunks: List[Dict]) -> Tuple[List[int], float]:
    """
    Return matching chunk_index list, plus best score (0..1) for debug.
    We do:
      - normalize both texts (lower + whitespace collapse + punctuation drop)
      - substring containment check
      - if none found, fallback to best SequenceMatcher ratio against full chunk text
    """
    fact_n = normalize_text(fact, drop_punct=True)
    if not fact_n:
        return ([], 0.0)

    matched = []
    for c in chunks:
        t = normalize_text(c.get("text", ""), drop_punct=True)
        if fact_n and fact_n in t:
            matched.append(int(c.get("chunk_index", 0)))

    if matched:
        return (sorted(set(matched)), 1.0)

    # Fallback: best approximate similarity (cheap heuristic; not sliding window)
    try:
        from difflib import SequenceMatcher

        best = 0.0
        best_idx = None
        for c in chunks:
            t = normalize_text(c.get("text", ""), drop_punct=True)
            ratio = SequenceMatcher(None, fact_n, t).ratio()
            if ratio > best:
                best = ratio
                best_idx = int(c.get("chunk_index", 0))
        if best_idx is not None and best >= 0.35:
            return ([best_idx], float(best))
        return ([], float(best))
    except Exception:
        return ([], 0.0)


async def build_qrels(
    qa_path: str,
    notebook_id: str,
    out_path: str,
    corpus_path: str = "",
) -> Dict:
    from app.database.milvus_client import MilvusService

    milvus = MilvusService()
    qa = load_json(qa_path)
    if not isinstance(qa, list):
        raise ValueError("QA file must be a JSON array")

    qrels = {}
    missing = []

    for qi, item in enumerate(qa):
        qid = f"query_{qi}"
        query_text = item.get("query", "")
        answer = item.get("answer", "")
        evidence_list = item.get("evidence_list") or []

        relevant = []

        for ev in evidence_list:
            url = ev.get("url", "")
            fact = ev.get("fact", "")
            doc_id = stable_doc_id_from_url(url)

            chunks = await milvus.get_chunks_by_document(doc_id)
            if not chunks:
                missing.append(
                    {
                        "query_id": qid,
                        "url": url,
                        "doc_id": doc_id,
                        "reason": "doc_not_found_in_milvus",
                    }
                )
                continue

            matched_indices, score = _match_fact_to_chunks(fact, chunks)
            if not matched_indices:
                missing.append(
                    {
                        "query_id": qid,
                        "url": url,
                        "doc_id": doc_id,
                        "reason": "fact_not_matched_to_any_chunk",
                        "best_score": score,
                        "fact": fact,
                    }
                )
                continue

            for chunk_idx in matched_indices:
                relevant.append(
                    {
                        "document_id": doc_id,
                        "chunk_index": int(chunk_idx),
                        "url": url,
                        "title": ev.get("title"),
                        "source": ev.get("source"),
                        "fact": fact,
                        "relevance": 1,
                    }
                )

        qrels[qid] = {
            "query_text": query_text,
            "answer": answer,
            "question_type": item.get("question_type"),
            "relevant_chunks": relevant,
        }

    out = {
        "notebook_id": notebook_id,
        "qa_path": qa_path,
        "corpus_path": corpus_path,
        "queries_count": len(qa),
        "qrels": qrels,
        "missing": missing,
    }
    save_json(out_path, out)
    return out


async def main_async():
    ensure_backend_on_path()

    p = argparse.ArgumentParser()
    p.add_argument("--qa", default="eval/sample_MultiHopRAG.json", help="Path to QA JSON")
    p.add_argument("--notebook-id", default="eval_multihoprag", help="Notebook id used in Milvus ingest")
    p.add_argument("--corpus", default="", help="Optional corpus path (for metadata only)")
    p.add_argument("--out", default="eval/results/qrels.json", help="Output qrels JSON path")
    args = p.parse_args()

    out = await build_qrels(
        qa_path=args.qa,
        notebook_id=args.notebook_id,
        out_path=args.out,
        corpus_path=args.corpus,
    )
    print(f"[qrels] saved to {args.out} queries={out['queries_count']} missing={len(out['missing'])}")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

