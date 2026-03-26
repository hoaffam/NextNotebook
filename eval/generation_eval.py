"""
Generation evaluation:
  (A) End-to-end QA: run the production workflow and compare answer vs ground-truth
  (B) Citation/grounding: coverage + validity + precision/recall vs evidence docs

NOTE: This eval requires LLM provider creds because the workflow includes LLM grading + generation.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from typing import Dict, List

from eval._common import ensure_backend_on_path, load_json
from eval.citation_evaluator import evaluate_citations


def _normalize_answer(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def exact_match(pred: str, gold: str) -> float:
    return 1.0 if _normalize_answer(pred) == _normalize_answer(gold) else 0.0


def token_f1(pred: str, gold: str) -> float:
    p = _normalize_answer(pred).split()
    g = _normalize_answer(gold).split()
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    common = {}
    for t in p:
        common[t] = common.get(t, 0) + 1
    overlap = 0
    for t in g:
        if common.get(t, 0) > 0:
            overlap += 1
            common[t] -= 1
    precision = overlap / len(p)
    recall = overlap / len(g)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


async def evaluate_generation(
    qa_path: str,
    notebook_id: str,
    out_path: str,
    sample_n: int = 50,
    enable_web_search: bool = False,
) -> Dict:
    from app.database.milvus_client import MilvusService
    from app.services.shared.embedding_service import EmbeddingService
    from app.services.shared.llm_service import get_llm_service
    from app.services.shared.web_search_service import get_web_search_service
    from app.services.shared.lexical_service import LexicalBM25Service
    from app.services.rag.workflow import create_rag_workflow

    qa = load_json(qa_path)
    if not isinstance(qa, list):
        raise ValueError("QA file must be a JSON array")

    if sample_n and sample_n > 0:
        qa = qa[:sample_n]

    milvus = MilvusService()
    embedding = EmbeddingService()
    llm = get_llm_service()
    web = get_web_search_service()
    lexical = LexicalBM25Service(milvus)

    workflow = create_rag_workflow(
        milvus_service=milvus,
        embedding_service=embedding,
        llm_service=llm,
        web_search_service=web,
        lexical_service=lexical,
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    samples_out = os.path.splitext(out_path)[0] + "_samples.jsonl"
    sf = open(samples_out, "w", encoding="utf-8")

    ems, f1s = [], []
    covs, vals, precs, recs = [], [], [], []

    for i, item in enumerate(qa):
        query = item.get("query", "")
        gold = item.get("answer", "")
        evidence_list = item.get("evidence_list") or []

        result = await workflow.ainvoke(
            {
                "question": query,
                "notebook_id": notebook_id,
                "chat_history": [],
                "force_web_search": bool(enable_web_search),
            }
        )

        pred = result.get("answer", "") or ""
        citations = result.get("citations", []) or []

        em = exact_match(pred, gold)
        f1 = token_f1(pred, gold)
        ems.append(em)
        f1s.append(f1)

        cite_metrics = evaluate_citations(pred, citations, evidence_list)
        covs.append(cite_metrics["citation_coverage"])
        vals.append(cite_metrics["citation_validity"])
        precs.append(cite_metrics["citation_precision"])
        recs.append(cite_metrics["citation_recall"])

        row = {
            "idx": i,
            "query": query,
            "gold_answer": gold,
            "pred_answer": pred,
            "qa_metrics": {"exact_match": em, "token_f1": f1},
            "citation_metrics": cite_metrics,
            "workflow_steps": result.get("steps", []),
            "used_web_search": result.get("used_web_search", False),
        }
        sf.write(json.dumps(row, ensure_ascii=False) + "\n")

        if (i + 1) % 10 == 0:
            print(f"[gen_eval] {i+1}/{len(qa)} done (EM={sum(ems)/(len(ems) or 1):.3f} F1={sum(f1s)/(len(f1s) or 1):.3f})")

    sf.close()

    summary = {
        "notebook_id": notebook_id,
        "qa_path": qa_path,
        "queries_tested": len(qa),
        "avg_exact_match": sum(ems) / len(ems) if ems else 0.0,
        "avg_token_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "avg_citation_coverage": sum(covs) / len(covs) if covs else 0.0,
        "avg_citation_validity": sum(vals) / len(vals) if vals else 0.0,
        "avg_citation_precision": sum(precs) / len(precs) if precs else 0.0,
        "avg_citation_recall": sum(recs) / len(recs) if recs else 0.0,
        "samples_jsonl": samples_out,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


async def main_async():
    ensure_backend_on_path()

    p = argparse.ArgumentParser()
    p.add_argument("--qa", default="eval/sample_MultiHopRAG.json")
    p.add_argument("--notebook-id", default="eval_multihoprag")
    p.add_argument("--sample", type=int, default=50)
    p.add_argument("--enable-web-search", action="store_true")
    p.add_argument("--out", default="eval/results/generation_summary.json")
    args = p.parse_args()

    summary = await evaluate_generation(
        qa_path=args.qa,
        notebook_id=args.notebook_id,
        out_path=args.out,
        sample_n=args.sample,
        enable_web_search=args.enable_web_search,
    )
    print(f"[gen_eval] summary saved to {args.out}")
    print(f"[gen_eval] samples saved to {summary['samples_jsonl']}")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

