# Eval (MultiHopRAG)

This folder contains an evaluation framework that **matches the project pipeline**:
- Chunking via `backend/app/core/text_chunker.py` (default `CHUNK_SIZE=1000`, `CHUNK_OVERLAP=200`)
- BM25 via `backend/app/services/shared/lexical_service.py`
- Vector search via `backend/app/database/milvus_client.py` + `backend/app/services/shared/embedding_service.py`
- Hybrid retrieval via **calling `GraphNodes.retrieve()` exactly** (`backend/app/services/rag/nodes.py`)
- End-to-end workflow via `create_rag_workflow()` (`backend/app/services/rag/workflow.py`)

## Dataset files
- `sample_corpus.json`: corpus (182 documents)
- `sample_MultiHopRAG.json`: QA set (170 questions with `evidence_list`)

## Key design: evidence facts vs chunk size
`evidence_list[*].fact` is a **short snippet**, much shorter than production chunks.
We map evidence to relevant chunks by:
- chunking the full article text with the production chunker
- normalizing both `fact` and chunk text (lowercase, punctuation drop, whitespace collapse)
- using **substring containment** to locate which chunk(s) contain the `fact`
- if not found, a small heuristic fallback selects the best chunk by approximate similarity

This produces **chunk-level qrels**: relevant keys are `(document_id, chunk_index)`.

## Scripts

### 1) Ingest corpus into Milvus
Creates embeddings and inserts all chunk vectors into Milvus under a dedicated `notebook_id`.

```bash
cd eval
python ingest_corpus.py --corpus eval/sample_corpus.json --notebook-id eval_multihoprag --reset
```

Outputs:
- `eval/results/manifest.json`

### 2) Prepare qrels (query → relevant chunks)

```bash
cd eval
python prepare_qrels.py --qa eval/sample_MultiHopRAG.json --notebook-id eval_multihoprag --out eval/results/qrels.json
```

Outputs:
- `eval/results/qrels.json` (includes a `missing` section for debugging unmapped evidence)

### 3) Retrieval evaluation (BM25 vs Vector vs Hybrid)

```bash
cd eval
python retrieval_eval.py --qrels eval/results/qrels.json --notebook-id eval_multihoprag --mode all --top-k 20
```

Outputs:
- `eval/results/retrieval_bm25_only.jsonl`
- `eval/results/retrieval_vector_only.jsonl`
- `eval/results/retrieval_hybrid_prod.jsonl`
- `eval/results/retrieval_summary.json`

Each `.jsonl` line contains per-query debug info:
- `document_id`, `chunk_index`, `_source`, `score_bm25(_norm)`, `score_emb_norm`, `score_combined`, `rank`, `is_relevant`.

### 4) Generation evaluation (end-to-end QA + citations)
Requires LLM credentials because the production workflow includes LLM grading + generation.

```bash
cd eval
python generation_eval.py --qa eval/sample_MultiHopRAG.json --notebook-id eval_multihoprag --sample 50
```

Outputs:
- `eval/results/generation_summary.json`
- `eval/results/generation_summary_samples.jsonl`

Metrics:
- QA: Exact Match, Token F1
- Citations: coverage, validity (token overlap with evidence facts), doc-level precision/recall vs evidence docs

### 5) One-shot runner

```bash
cd eval
python run_eval.py --mode all --corpus eval/sample_corpus.json --qa eval/sample_MultiHopRAG.json --notebook-id eval_multihoprag --reset
```

## Notes
- `document_id` is derived from URL using a stable SHA1 hash (Milvus field limit is 128 chars).
- If you want to run only BM25 retrieval without embeddings, run `retrieval_eval.py --mode bm25_only` and skip ingest if you already have chunks available.
