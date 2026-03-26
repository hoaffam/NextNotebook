"""
Main orchestration script for the eval pipeline.

Recommended flow:
  1) ingest_corpus.py (one-time) -> writes eval/results/manifest.json
  2) prepare_qrels.py            -> writes eval/results/qrels.json
  3) retrieval_eval.py           -> writes retrieval_summary + per-query jsonl
  4) generation_eval.py          -> writes generation_summary + per-sample jsonl

This script provides a single entrypoint to run subsets of the above.
"""

from __future__ import annotations

import argparse
import asyncio
import os

from eval._common import ensure_backend_on_path


async def main_async():
    ensure_backend_on_path()

    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="all", choices=["all", "ingest", "qrels", "retrieval", "generation"])
    p.add_argument("--corpus", default="eval/sample_corpus.json")
    p.add_argument("--qa", default="eval/sample_MultiHopRAG.json")
    p.add_argument("--notebook-id", default="eval_multihoprag")
    p.add_argument("--reset", action="store_true", help="Reset notebook vectors before ingest")
    p.add_argument("--limit-docs", type=int, default=0)
    p.add_argument("--sample", type=int, default=50, help="Generation eval sample size")
    p.add_argument("--top-k", type=int, default=20)
    p.add_argument("--enable-web-search", action="store_true")
    p.add_argument("--out-dir", default="eval/results")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    if args.mode in ["all", "ingest"]:
        from eval.ingest_corpus import ingest_corpus
        from eval._common import save_json

        manifest = await ingest_corpus(
            corpus_path=args.corpus,
            notebook_id=args.notebook_id,
            limit_docs=args.limit_docs,
            reset_notebook=args.reset,
        )
        save_json(os.path.join(args.out_dir, "manifest.json"), manifest)

    if args.mode in ["all", "qrels"]:
        from eval.prepare_qrels import build_qrels

        await build_qrels(
            qa_path=args.qa,
            notebook_id=args.notebook_id,
            out_path=os.path.join(args.out_dir, "qrels.json"),
            corpus_path=args.corpus,
        )

    if args.mode in ["all", "retrieval"]:
        from eval.retrieval_eval import evaluate_mode
        import json

        qrels_path = os.path.join(args.out_dir, "qrels.json")
        summary = {"notebook_id": args.notebook_id, "qrels": qrels_path, "top_k": args.top_k, "modes": {}}
        for mode in ["bm25_only", "vector_only", "hybrid_prod"]:
            out_jsonl = os.path.join(args.out_dir, f"retrieval_{mode}.jsonl")
            res = await evaluate_mode(qrels_path, args.notebook_id, mode, args.top_k, out_jsonl)
            summary["modes"][mode] = res
        with open(os.path.join(args.out_dir, "retrieval_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    if args.mode in ["all", "generation"]:
        from eval.generation_eval import evaluate_generation

        await evaluate_generation(
            qa_path=args.qa,
            notebook_id=args.notebook_id,
            out_path=os.path.join(args.out_dir, "generation_summary.json"),
            sample_n=args.sample,
            enable_web_search=args.enable_web_search,
        )


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

