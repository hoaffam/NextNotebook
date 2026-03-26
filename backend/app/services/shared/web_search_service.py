"""
Web Search Service
Search the web using Tavily API for RAG enhancement
"""

from typing import List, Dict, Optional
import httpx
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class WebSearchService:
    """Service for web search using Tavily API"""

    def __init__(self):
        """Initialize Tavily client"""
        self.api_key = getattr(settings, 'TAVILY_API_KEY', None)
        self.base_url = "https://api.tavily.com"
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("Tavily API key not configured. Web search disabled.")
        else:
            logger.info("Tavily web search service initialized")

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",  # "basic" or "advanced"
        include_domains: List[str] = None,
        exclude_domains: List[str] = None
    ) -> Dict:
        """
        Search the web using Tavily API

        Args:
            query: Search query
            max_results: Maximum number of results (1-10)
            search_depth: "basic" (faster) or "advanced" (more thorough)
            include_domains: Only search these domains
            exclude_domains: Exclude these domains

        Returns:
            Dict with search results and answer
        """
        if not self.enabled:
            logger.warning("Web search called but Tavily API key not configured")
            return {
                "results": [],
                "answer": None,
                "query": query,
                "error": "Web search not configured"
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": min(max_results, 10),
                    "search_depth": search_depth,
                    "include_answer": True,
                    "include_raw_content": False
                }

                if include_domains:
                    payload["include_domains"] = include_domains
                if exclude_domains:
                    payload["exclude_domains"] = exclude_domains

                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload
                )

                if response.status_code != 200:
                    logger.error(f"Tavily search failed: {response.status_code} - {response.text}")
                    return {
                        "results": [],
                        "answer": None,
                        "query": query,
                        "error": f"Search failed: {response.status_code}"
                    }

                data = response.json()

                # Process results
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                        "score": item.get("score", 0)
                    })

                logger.info(f"Tavily search returned {len(results)} results for: {query[:50]}...")

                return {
                    "results": results,
                    "answer": data.get("answer"),
                    "query": query,
                    "error": None
                }

        except httpx.TimeoutException:
            logger.error("Tavily search timeout")
            return {
                "results": [],
                "answer": None,
                "query": query,
                "error": "Search timeout"
            }
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return {
                "results": [],
                "answer": None,
                "query": query,
                "error": str(e)
            }

    async def search_for_rag(
        self,
        query: str,
        max_results: int = 3
    ) -> List[Dict]:
        """
        Search web and format results for RAG context

        Returns list of documents formatted like local search results
        """
        search_result = await self.search(query, max_results=max_results)

        if search_result.get("error"):
            return []

        # Format results as RAG documents
        rag_documents = []
        for i, result in enumerate(search_result.get("results", [])):
            rag_documents.append({
                "id": f"web_{i}",
                "document_id": "web_search",
                "filename": result.get("url", "web"),
                "chunk_index": i,
                "text": f"{result.get('title', '')}\n\n{result.get('content', '')}",
                "score": result.get("score", 0),
                "source_type": "web",
                "url": result.get("url", ""),
                "title": result.get("title", "")
            })

        return rag_documents

    def is_enabled(self) -> bool:
        """Check if web search is enabled"""
        return self.enabled


# Singleton instance
_web_search_service = None

def get_web_search_service() -> WebSearchService:
    """Get singleton WebSearchService instance"""
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service
