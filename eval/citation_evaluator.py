"""
Citation evaluation utilities.

We evaluate:
  - coverage: % sentences containing at least one [cid:X]
  - validity: % cited ids that exist in citations list AND have token overlap with ground-truth evidence facts
  - precision/recall vs evidence docs (by hashed doc_id from evidence urls)
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

from eval._common import normalize_text, stable_doc_id_from_url


_re_cid = re.compile(r"\[cid:(\d+)\]")


def extract_citation_ids(answer: str) -> List[int]:
    if not answer:
        return []
    return [int(x) for x in _re_cid.findall(answer)]


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    # Simple sentence split; good enough for coverage proxy
    parts = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    return [p for p in parts if p]


def sentence_has_citation(sentence: str) -> bool:
    return bool(_re_cid.search(sentence or ""))


def token_overlap(a: str, b: str) -> int:
    a_n = normalize_text(a, drop_punct=True)
    b_n = normalize_text(b, drop_punct=True)
    a_tokens = set(a_n.split())
    b_tokens = set(b_n.split())
    return len(a_tokens & b_tokens)


def evaluate_citations(
    answer: str,
    citations: List[Dict],
    evidence_list: List[Dict],
    overlap_threshold: int = 30,
) -> Dict:
    used_ids = extract_citation_ids(answer)
    used_set = set(used_ids)

    sentences = split_sentences(answer)
    if sentences:
        coverage = sum(1 for s in sentences if sentence_has_citation(s)) / len(sentences)
    else:
        coverage = 0.0

    # Build citation_id -> citation object
    by_id = {int(c.get("citation_id")): c for c in citations if c.get("citation_id") is not None}

    # Build evidence facts as one pool
    evidence_facts = [e.get("fact", "") for e in (evidence_list or []) if e.get("fact")]
    evidence_docs = set(stable_doc_id_from_url(e.get("url", "")) for e in (evidence_list or []) if e.get("url"))

    valid = 0
    for cid in used_set:
        c = by_id.get(cid)
        if not c:
            continue
        chunk_text = c.get("raw_text", "") or ""
        best_overlap = 0
        for fact in evidence_facts:
            best_overlap = max(best_overlap, token_overlap(chunk_text, fact))
        if best_overlap >= overlap_threshold:
            valid += 1

    validity = (valid / len(used_set)) if used_set else 0.0

    cited_docs = set()
    for cid in used_set:
        c = by_id.get(cid)
        if c and c.get("document_id"):
            cited_docs.add(str(c.get("document_id")))

    # Precision/recall against evidence docs (doc-level)
    inter = cited_docs & evidence_docs
    precision = (len(inter) / len(cited_docs)) if cited_docs else 0.0
    recall = (len(inter) / len(evidence_docs)) if evidence_docs else 0.0

    return {
        "citation_coverage": coverage,
        "citation_validity": validity,
        "citation_precision": precision,
        "citation_recall": recall,
        "num_citations_used": len(used_set),
        "used_ids": sorted(list(used_set)),
    }

