from typing import List, Dict
from rank_bm25 import BM25Okapi


class LexicalBM25Service:
    """
    Simple lexical BM25 service built on top of Milvus chunk corpus.
    """

    def __init__(self, milvus_service):
        self.milvus = milvus_service

    async def search(self, question: str, notebook_id: str, top_k: int = 20) -> List[Dict]:
        # Fetch all chunks for the notebook
        corpus_docs = await self.milvus.get_all_chunks(notebook_id)
        if not corpus_docs:
            return []

        corpus = [(d.get("text") or "") for d in corpus_docs]
        tokenized = [c.split() for c in corpus]
        if not any(tokenized):
            return []

        bm25 = BM25Okapi(tokenized)
        bm_scores = bm25.get_scores((question or "").split())

        results = []
        for doc, bm in zip(corpus_docs, bm_scores):
            doc_copy = dict(doc)
            doc_copy["score_bm25"] = bm
            results.append(doc_copy)

        results = sorted(results, key=lambda d: d.get("score_bm25", 0), reverse=True)[:top_k]
        return results

