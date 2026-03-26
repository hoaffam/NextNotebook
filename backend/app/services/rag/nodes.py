"""
Graph Nodes
Node functions for the Corrective RAG (CRAG) LangGraph workflow
"""

from typing import Dict, List
import re
from app.services.rag.state import GraphState
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class GraphNodes:
    """
    Node functions for the CRAG workflow

    Each node takes state and returns updated state
    """

    def __init__(self, milvus_service, embedding_service, llm_service, web_search_service=None, lexical_service=None):
        self.milvus = milvus_service
        self.embedding = embedding_service
        self.llm = llm_service
        self.web_search_svc = web_search_service  # Renamed to avoid conflict with method
        self.lexical = lexical_service  # Optional lexical/BM25 service

    async def retrieve(self, state: GraphState) -> Dict:
        """
        Retrieve relevant documents from Milvus

        Input: question, notebook_id
        Output: documents
        """
        logger.info("--- RETRIEVE NODE ---")

        question = state.get("rewritten_question") or state["question"]
        notebook_id = state["notebook_id"]

        logger.info(f"Searching for notebook_id: {notebook_id}")
        logger.info(f"Query: {question[:100]}...")

        # --- Lexical search first (if configured) ---
        lexical_docs = []
        if self.lexical:
            try:
                lexical_docs = await self.lexical.search(question, notebook_id, top_k=20)
                # Log top lexical hits (up to 20)
                for i, doc in enumerate(lexical_docs[:20]):
                    logger.info(
                        f"[retrieve] lexical doc#{i+1} id={doc.get('document_id','?')} "
                        f"file={doc.get('filename','?')} "
                        f"bm25={doc.get('score_bm25','n/a')} "
                        f"text_full={doc.get('text','')}"
                    )
                for d in lexical_docs:
                    if "score_bm25" not in d:
                        d["score_bm25"] = d.get("score", 0) or 0
            except Exception as e:
                logger.warning(f"[retrieve] lexical search failed: {e}")
        else:
            logger.info("[retrieve] routing=lexical_skipped (no lexical service)")

        # --- Vector search (fallback/augment) ---
        query_embedding = await self.embedding.embed_query(question)
        vector_docs = await self.milvus.search(
            query_embedding=query_embedding,
            notebook_id=notebook_id,
            top_k=20
        )

        routing = "lexical+vector" if lexical_docs else "vector_only"

        # --- Normalize, boost, merge ---
        bm_scores = [d.get("score_bm25", 0) or 0 for d in lexical_docs]
        emb_scores = [d.get("score", 0) or 0 for d in vector_docs]
        bm_top = max(bm_scores) if bm_scores else 0.0
        max_emb = max(emb_scores) if emb_scores else 1e-6

        # Dynamic alpha based on BM25 confidence
        bm_conf = bm_top / (bm_top + 1e-6) if bm_top > 0 else 0.0
        if bm_conf >= 0.8:
            alpha = 0.3  # favor lexical when strong BM25
        elif bm_conf >= 0.5:
            alpha = 0.5
        else:
            alpha = 0.7  # favor embedding when BM25 weak

        combined_docs = []
        q_tokens = (question or "").split()

        def phrase_boost(doc_text: str, q: str, bm_norm: float, max_boost: float = 0.1) -> float:
            doc_tokens = (doc_text or "").lower().split()
            q_tokens_local = (q or "").lower().split()
            if len(q_tokens_local) < 2:
                return bm_norm
            phrase_local = " ".join(q_tokens_local[:2])
            if phrase_local and phrase_local in " ".join(doc_tokens):
                bm_norm += 0.05
            overlap = sum(1 for t in q_tokens_local if t in doc_tokens)
            ratio = overlap / max(1, len(set(q_tokens_local)))
            bm_norm += min(max_boost, 0.05 * ratio)
            return min(1.0, bm_norm)

        def combine_doc(doc, bm, emb, source: str):
            emb_norm = emb / (max_emb + 1e-6)
            bm_norm = bm / (bm_top + 1e-6) if bm_top > 0 else 0.0
            bm_norm = phrase_boost(doc.get("text", ""), question, bm_norm)
            combined_score = alpha * emb_norm + (1 - alpha) * bm_norm
            doc["score_emb_norm"] = emb_norm
            doc["score_bm25_norm"] = bm_norm
            doc["score_combined"] = combined_score
            doc["_source"] = source  # track lexical/vector for dedup priority
            return doc

        # Keep top lexical before merge (guaranteed keepers)
        top_k_lex_keep = 10
        for doc in lexical_docs[:top_k_lex_keep]:
            combined_docs.append(combine_doc(doc, doc.get("score_bm25", 0) or 0, doc.get("score", 0) or 0, "lexical"))
        for doc in lexical_docs[top_k_lex_keep:]:
            combined_docs.append(combine_doc(doc, doc.get("score_bm25", 0) or 0, doc.get("score", 0) or 0, "lexical"))
        for doc in vector_docs:
            combined_docs.append(combine_doc(doc, doc.get("score_bm25", 0) or 0, doc.get("score", 0) or 0, "vector"))

        dedup = {}
        for doc in combined_docs:
            key = (doc.get("document_id"), doc.get("chunk_index"))
            if key not in dedup:
                dedup[key] = doc
            else:
                # lexical wins; otherwise higher combined
                if doc.get("_source") == "lexical" and dedup[key].get("_source") != "lexical":
                    dedup[key] = doc
                elif doc.get("score_combined", 0) > dedup[key].get("score_combined", 0):
                    dedup[key] = doc
        merged = list(dedup.values())

        top_k = 20
        documents = sorted(merged, key=lambda d: d.get("score_combined", 0), reverse=True)[:top_k]

        for i, doc in enumerate(documents):
            logger.info(
                f"[retrieve] routing={routing} doc#{i+1} id={doc.get('document_id','?')} "
                f"file={doc.get('filename','?')} "
                f"bm25_norm={doc.get('score_bm25_norm','n/a')} "
                f"emb_norm={doc.get('score_emb_norm','n/a')} "
                f"combined={doc.get('score_combined','n/a')} "
                f"text_preview={doc.get('text','')[:200].replace(chr(10), ' ')}"
            )
            
        retrieval_count = state.get("retrieval_count", 0) + 1

        logger.info(f"Retrieved {len(documents)} documents")

        return {
            "documents": documents,
            "steps": ["retrieve"],
            "retrieval_count": retrieval_count
        }

    async def grade_documents(self, state: GraphState) -> Dict:
        """
        Grade retrieved documents for relevance

        Input: documents, question
        Output: filtered_documents, web_search_needed
        """
        logger.info("--- GRADE DOCUMENTS NODE ---")

        question = state["question"]
        documents = state.get("documents", [])

        # Default quality signals
        default_resp = {
            "filtered_documents": [],
            "web_search_needed": False,
            "steps": ["grade_documents"],
            "coverage_score": 0.0,
            "answerable": False,
            "citable": False,
        }

        if not documents:
            logger.info("No documents retrieved; keep web_search_needed=True")
            default_resp["web_search_needed"] = True
            return default_resp

        # Use LLM to grade relevance
        try:
            # sort document by chunk_index for consistent grading order
            documents = sorted(documents, key=lambda d: d.get("chunk_index", 0))
            doc_texts = [d.get("text", "") for d in documents]
            relevance_scores = await self.llm.grade_documents(question, doc_texts)
        except Exception as e:
            logger.warning(f"grade_documents failed, fallback to all docs: {e}")
            for d in documents:
                d["score"] = d.get("score", 0)
            default_resp["filtered_documents"] = documents
            return default_resp

        # Attach scores to documents
        for doc, score in zip(documents, relevance_scores):
            doc["score"] = score
            logger.info(
                f"Rel score={score:.3f}"
            )

        # Soft threshold relative to top-1 to avoid clamped percentiles (BM25 not normalized)
        scores = [d.get("score", 0) or 0 for d in documents]
        if scores:
            top1 = max(scores)
            soft_thr = top1 * 0.6 if top1 > 0 else 0.1
        else:
            soft_thr = 0.3

        filtered = [d for d in documents if (d.get("score", 0) or 0) >= soft_thr]

        # # If empty after soft filter, fallback to top-2 by score
        # if not filtered:
        #     filtered = sorted(documents, key=lambda d: d.get("score", 0) or 0, reverse=True)[:2]

        # Quality signals
        if filtered:
            sorted_scores = sorted((d.get("score", 0) or 0) for d in filtered)
            topk = sorted_scores[-3:] if len(sorted_scores) >= 3 else sorted_scores
            coverage_score = sum(topk) / len(topk)
            best_rel = sorted_scores[-1]
        else:
            coverage_score = 0.0
            best_rel = 0.0

        # answerable: combine coverage + count + best_rel
        answerable = (coverage_score >= 0.5) or (len(filtered) >= 2 and best_rel >= 0.35)

        # citable: prefer overlap_tokens, else fallback to score+text availability
        citable = any((d.get("overlap_tokens", 0) or 0) >= 30 for d in filtered)
        if not citable:
            citable = any((d.get("score", 0) or 0) >= 0.5 and d.get("text") for d in filtered)

        # web_search_needed: only when no docs or quality very low
        web_search_needed = (len(filtered) == 0) or (coverage_score < 0.25 and best_rel < 0.25)

        logger.info(
            f"Filtered={len(filtered)}/{len(documents)} soft_thr={soft_thr:.3f} "
            f"best_rel={best_rel:.3f} coverage={coverage_score:.3f} "
            f"answerable={answerable} citable={citable} web_search_needed={web_search_needed}"
        )

        return {
            "filtered_documents": filtered,
            "web_search_needed": web_search_needed,
            "steps": ["grade_documents"],
            "coverage_score": coverage_score,
            "answerable": answerable,
            "citable": citable,
        }

    async def rewrite_query(self, state: GraphState) -> Dict:
        """
        Rewrite the query for better retrieval

        Input: question
        Output: rewritten_question
        """
        logger.info("--- REWRITE QUERY NODE ---")

        question = state["question"]

        # Rewrite using LLM
        rewritten = await self.llm.rewrite_query(question)

        logger.info(f"Rewritten query: {rewritten}")

        return {
            "rewritten_question": rewritten,
            "steps": ["rewrite_query"]
        }

    async def web_search(self, state: GraphState) -> Dict:
        """
        Perform web search using Tavily for additional information

        Input: question
        Output: web_results, web_sources
        """
        logger.info("--- WEB SEARCH NODE (Tavily) ---")

        if not self.web_search_svc or not self.web_search_svc.is_enabled():
            logger.warning("Web search service not configured or disabled")
            return {
                "web_results": [],
                "web_sources": [],
                "used_web_search": False,
                "steps": ["web_search_skipped"]
            }

        question = state.get("rewritten_question") or state["question"]

        # Limit query length for Tavily (max 400 chars)
        if len(question) > 380:
            question = state["question"][:380]  # Use original question if rewritten is too long

        # Search the web using Tavily
        search_result = await self.web_search_svc.search(question, max_results=5)

        if search_result.get("error"):
            logger.warning(f"Web search failed: {search_result.get('error')}")
            return {
                "web_results": [],
                "web_sources": [],
                "used_web_search": False,
                "steps": ["web_search_failed"]
            }

        # Format results for RAG context
        web_results = []
        web_sources = []

        for result in search_result.get("results", []):
            # For RAG context
            web_results.append({
                "text": f"{result.get('title', '')}\n\n{result.get('content', '')}",
                "source_type": "web"
            })

            # For UI display
            web_sources.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", "")[:300],  # Preview
                "score": result.get("score", 0)
            })

        logger.info(f"Found {len(web_results)} web results from Tavily")

        return {
            "web_results": web_results,
            "web_sources": web_sources,
            "used_web_search": True,
            "steps": ["web_search"]
        }

    async def generate(self, state: GraphState) -> Dict:
        """
        Generate final answer using 3-step citation flow:
        1. Generate content-only answer (focus on quality)
        2. Add citations to answer (focus on accuracy)
        3. Validate citations (quality control)

        Input: question, filtered_documents, web_results, chat_history
        Output: answer, sources, web_sources
        """
        logger.info("--- GENERATE NODE (3-STEP CRAG) ---")

        question = state["question"]
        documents = state.get("filtered_documents", [])
        web_results = state.get("web_results", [])
        web_sources = state.get("web_sources", [])
        chat_history = state.get("chat_history", [])
        used_web_search = state.get("used_web_search", False)

        # Build context from documents and enhanced citations
        context_parts = []
        citations = []  # Enhanced citations with full metadata
        citation_id = 1

        logger.info(f"Building citations from {len(documents)} documents")

        if documents:
            context_parts.append("=== Thông tin từ tài liệu của bạn ===")
            # sort document by chunk_index for consistent context order
            docs_sorted = sorted(documents, key=lambda d: d.get("chunk_index", 0))
            for doc in docs_sorted:
                idx = doc.get("chunk_index", 0)
                doc_id = doc.get("document_id", "")
                context_parts.append(f"[chunk {idx} | doc {doc_id} | file {doc.get('filename','')}]")
                context_parts.append(doc.get("text", ""))

                # Create enhanced citation
                file_type = doc.get("file_type", "txt")
                logger.info(f"Creating citation {citation_id} - file_type: {file_type}, filename: {doc.get('filename')}")
                citation = {
                    "citation_id": citation_id,
                    "document_id": doc.get("document_id", ""),
                    "filename": doc.get("filename", ""),
                    "file_type": file_type,
                    "raw_text": doc.get("text", ""),
                    "chunk_index": doc.get("chunk_index", 0),
                    "relevance_score": doc.get("score", 0),
                    "source_type": "document"
                }

                # Add file-type-specific citation metadata
                if file_type == "pdf":
                    citation.update({
                        "page_number": doc.get("page_number"),
                        "paragraph_start": doc.get("paragraph_start"),
                        "paragraph_end": doc.get("paragraph_end"),
                        "char_start": doc.get("char_start"),
                        "char_end": doc.get("char_end")
                    })
                    # Format citation text
                    page = doc.get("page_number", "?")
                    citation["citation_text"] = f"[{citation_id}] {doc.get('filename', '')}, page {page}"

                elif file_type == "docx":
                    citation.update({
                        "heading": doc.get("heading"),
                        "heading_level": doc.get("heading_level"),
                        "section_path": doc.get("section_path"),
                        "is_table": doc.get("is_table", False),
                        "table_name": doc.get("table_name"),
                        "paragraph_start": doc.get("paragraph_start"),
                        "paragraph_end": doc.get("paragraph_end"),
                        "char_start": doc.get("char_start"),
                        "char_end": doc.get("char_end")
                    })
                    # Format citation text
                    heading = doc.get("heading", "(No Heading)")
                    if doc.get("is_table"):
                        table_name = doc.get("table_name", "Table")
                        citation["citation_text"] = f"[{citation_id}] {doc.get('filename', '')}, {table_name}"
                    else:
                        citation["citation_text"] = f"[{citation_id}] {doc.get('filename', '')}, '{heading}'"

                elif file_type == "txt":
                    citation.update({
                        "line_start": doc.get("line_start"),
                        "line_end": doc.get("line_end"),
                        "paragraph_start": doc.get("paragraph_start"),
                        "paragraph_end": doc.get("paragraph_end")
                    })
                    # Format citation text
                    line_start = doc.get("line_start", "?")
                    line_end = doc.get("line_end", "?")
                    citation["citation_text"] = f"[{citation_id}] {doc.get('filename', '')}, lines {line_start}-{line_end}"

                # Log citation metadata for debugging
                logger.info(f"Citation {citation_id} metadata: page={citation.get('page_number')}, heading={citation.get('heading')}, lines={citation.get('line_start')}-{citation.get('line_end')}")

                citations.append(citation)
                citation_id += 1

        logger.info(f"Total citations created: {len(citations)}")

        # Build citation catalog for LLM enforcement
        citation_catalog = ""
        if citations:
            def _format_location(c: Dict) -> str:
                ftype = c.get("file_type")
                if ftype == "pdf":
                    return f"page {c.get('page_number', '?')}"
                if ftype == "docx":
                    if c.get("is_table"):
                        return c.get("table_name", "table")
                    return c.get("heading", "heading")
                if ftype == "txt":
                    return f"lines {c.get('line_start', '?')}-{c.get('line_end', '?')}"
                return ""

            catalog_lines = []
            for c in citations:
                # truncate raw text to feed to LLM
                raw = c.get("raw_text", "").replace("\n", " ")
                max_chars = min(int(len(raw) * 1.1), 1200)
                preview = raw[:max_chars].replace("\n", " ")
                
                catalog_lines.append(
                    f"- [cid:{c['citation_id']}] {c.get('filename', '')} | {c.get('file_type', '?')} | "
                    f"{_format_location(c)} | chunk {c.get('chunk_index', '?')} | score {(c.get('relevance_score') or 0):.2f} | {preview}"
                )
            citation_catalog = "\n".join(catalog_lines)

        # Add web results to context if available
        if web_results:
            context_parts.append("\n\n=== Thông tin bổ sung từ web ===")
            for result in web_results:
                context_parts.append(result.get("text", ""))

        context = "\n\n".join(context_parts)

        # Determine response style based on sources
        if not documents and not web_results:
            # No sources at all
            context = "Không tìm thấy thông tin liên quan trong tài liệu hoặc trên web."

        # Log final context for debugging
        logger.info(f"Check final context feed to LLM: {context[:500]}...")

        # === 3-STEP CITATION FLOW ===
        
        # Step 1: Generate content-only answer (no citations)
        logger.info("[Step 1/3] Generating base answer without citations...")
        base_answer = await self.llm.generate_answer_without_citations(
            question=question,
            context=context,
            chat_history=chat_history
        )
        logger.info(f"[Step 1/3] Base answer generated: {base_answer[:200]}...")
        
        # Step 2: Add citations to answer
        if citations:
            logger.info(f"[Step 2/3] Adding citations to answer ({len(citations)} available)...")
            answer = await self.llm.add_citations_to_answer(
                base_answer=base_answer,
                citation_catalog=citation_catalog
            )
            logger.info(f"[Step 2/3] Answer with citations: {answer[:200]}...")
        else:
            logger.info("[Step 2/3] Skipped (no citations available)")
            answer = base_answer
        
        # Step 3: Validate citations
        from app.services.shared.citation_policy import validate_citations
        
        logger.info("[Step 3/3] Validating citations...")
        allowed_ids = [c["citation_id"] for c in citations]
        validation = validate_citations(answer, allowed_ids)
        
        if validation["has_unknown"]:
            logger.warning(f"[Step 3/3] Answer used UNKNOWN citation ids: {validation['unknown_ids']}")
        
        if validation["used_ids"]:
            logger.info(f"[Step 3/3] Valid citations used: {validation['used_ids']}")
            citations = [c for c in citations if c["citation_id"] in set(validation["used_ids"])]
        else:
            logger.warning("[Step 3/3] No valid inline citations detected in answer.")

        # Backward compatible sources aligned with (possibly filtered) citations
        sources = [{
            "document_id": c["document_id"],
            "filename": c["filename"],
            "chunk_index": c["chunk_index"],
            "text_preview": c["raw_text"][:200],
            "relevance_score": c["relevance_score"],
            "source_type": "document"
        } for c in citations]

        logger.info(f"Generated answer using {len(citations)} cited docs + {len(web_sources)} web sources")

        return {
            "answer": answer,
            "sources": sources,  # Backward compatible format
            "citations": citations,  # Enhanced citations with metadata
            "web_sources": web_sources,
            "used_web_search": used_web_search,
            "steps": ["generate"]
        }
