"""
Ingest MultiHopRAG corpus into Milvus under a dedicated notebook_id for evaluation.

This script uses the SAME chunker (TextChunker) and embedding service as production.
It stores each article as a separate "document" in Milvus, using a stable hash-based document_id derived from URL.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Dict, List

from eval._common import ensure_backend_on_path, load_json, save_json, stable_doc_id_from_url, safe_first


def _build_chunks(body: str) -> List[Dict]:
    from app.core.text_chunker import TextChunker

    chunker = TextChunker()
    chunks = chunker.chunk_text(body or "")
    for c in chunks:
        c["file_type"] = "txt"
    return chunks


async def ingest_corpus(
    corpus_path: str,
    notebook_id: str,
    limit_docs: int = 0,
    reset_notebook: bool = False,
) -> Dict:
    from app.database.milvus_client import MilvusService
    from app.services.shared.embedding_service import EmbeddingService

    milvus = MilvusService()
    embedding = EmbeddingService()

    if reset_notebook:
        await milvus.delete_notebook_documents(notebook_id)

    corpus = load_json(corpus_path)
    if not isinstance(corpus, list):
        raise ValueError("Corpus must be a JSON array")

    if limit_docs and limit_docs > 0:
        corpus = corpus[:limit_docs]

    manifest_docs = []
    total_chunks = 0

    for idx, article in enumerate(corpus):
        url = article.get("url", "")
        title = article.get("title", "") or "Untitled"
        body = article.get("body", "")

        doc_id = stable_doc_id_from_url(url)
        chunks = _build_chunks(body)
        texts = [c["text"] for c in chunks]

        # Embeddings per chunk (Gemini embed_content; can be slow)
        embeddings = await embedding.embed_texts(texts)

        ok = await milvus.insert_documents(
            doc_id=doc_id,
            notebook_id=notebook_id,
            filename=title,
            chunks=chunks,
            embeddings=embeddings,
        )
        if not ok:
            raise RuntimeError(f"Failed to insert doc_id={doc_id} title={title}")

        total_chunks += len(chunks)
        manifest_docs.append(
            {
                "doc_id": doc_id,
                "url": url,
                "title": title,
                "source": article.get("source"),
                "category": article.get("category"),
                "published_at": article.get("published_at"),
                "chunks_count": len(chunks),
                "body_preview": safe_first(body, 160),
            }
        )

        if (idx + 1) % 10 == 0:
            print(f"[ingest] {idx+1}/{len(corpus)} docs inserted (chunks_total={total_chunks})")

    manifest = {
        "notebook_id": notebook_id,
        "corpus_path": corpus_path,
        "docs_count": len(manifest_docs),
        "chunks_count": total_chunks,
        "docs": manifest_docs,
    }
    return manifest


async def main_async():
    ensure_backend_on_path()

    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="eval/sample_corpus.json", help="Path to corpus JSON")
    parser.add_argument("--notebook-id", default="eval_multihoprag", help="Notebook id to use in Milvus")
    parser.add_argument("--limit-docs", type=int, default=0, help="Limit docs ingested (0 = all)")
    parser.add_argument("--reset", action="store_true", help="Delete existing vectors for this notebook_id before ingest")
    parser.add_argument("--out", default="eval/results/manifest.json", help="Where to write manifest JSON")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    manifest = await ingest_corpus(
        corpus_path=args.corpus,
        notebook_id=args.notebook_id,
        limit_docs=args.limit_docs,
        reset_notebook=args.reset,
    )

    save_json(args.out, manifest)
    print(f"[ingest] done notebook_id={manifest['notebook_id']} docs={manifest['docs_count']} chunks={manifest['chunks_count']}")
    print(f"[ingest] manifest saved to {args.out}")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

