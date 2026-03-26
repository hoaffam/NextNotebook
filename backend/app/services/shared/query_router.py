"""
Query Router Service
Hybrid routing: fast rule-based detection first, LLM classifier fallback for ambiguity.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryRouter:
    def __init__(self, llm_service=None):
        self.llm = llm_service

        # Rule patterns (Vietnamese + English)
        self._greeting = re.compile(
            r"^\s*(hi|hello|hey|xin chào|chào|alo|good morning|good afternoon|good evening|bye|tạm biệt)\b",
            re.IGNORECASE,
        )
        self._meta = re.compile(
            r"(bạn là ai|bạn làm được gì|help me|how do you work|có thể làm gì|hướng dẫn|cách dùng|usage|capabilities)",
            re.IGNORECASE,
        )
        self._chitchat = re.compile(
            r"(bạn khỏe không|how are you|tên bạn là gì|what is your name|mấy giờ|thời tiết|weather)",
            re.IGNORECASE,
        )

    async def route_query(self, query: str, chat_history: Optional[List] = None) -> Dict:
        """
        Returns:
          - route: greeting|chitchat|meta|out_of_scope|retrieval_needed
          - method: rule|llm
          - confidence: float
        """
        q = (query or "").strip()

        rule = self._try_rule_based(q)
        if rule.get("matched"):
            return {"route": rule["route"], "method": "rule", "confidence": 1.0}

        llm_result = await self._llm_classify(q, chat_history or [])
        return {"route": llm_result["route"], "method": "llm", "confidence": llm_result.get("confidence", 0.7)}

    def _try_rule_based(self, query: str) -> Dict:
        if not query:
            return {"matched": True, "route": "chitchat"}

        if self._greeting.search(query):
            return {"matched": True, "route": "greeting"}
        if self._chitchat.search(query):
            return {"matched": True, "route": "chitchat"}
        if self._meta.search(query):
            return {"matched": True, "route": "meta"}

        return {"matched": False}

    async def _llm_classify(self, query: str, chat_history: List) -> Dict:
        """
        LLM-based fallback classifier for ambiguity.
        We classify into:
          - retrieval_needed: likely asks about notebook/doc content
          - out_of_scope: generic/off-topic unrelated to notebook
          - chitchat/meta: conversational
        """
        if not self.llm:
            # Conservative fallback: run retrieval
            return {"route": "retrieval_needed", "confidence": 0.5}

        # Keep history very short to avoid token waste; only include last user message if any
        last_user = ""
        try:
            for msg in reversed(chat_history[-5:]):
                role = getattr(msg, "role", None) or msg.get("role")
                if role == "user":
                    last_user = getattr(msg, "content", None) or msg.get("content", "")
                    break
        except Exception:
            last_user = ""

        prompt = f"""Bạn là bộ phân loại routing cho chatbot NotebookLM-style.

Hãy chọn 1 nhãn duy nhất trong các nhãn sau:
- greeting: lời chào/tạm biệt
- chitchat: trò chuyện xã giao, không cần tìm tài liệu
- meta: hỏi về khả năng/cách dùng hệ thống
- out_of_scope: câu hỏi không liên quan notebook, nên nhắc user hỏi về tài liệu
- retrieval_needed: câu hỏi cần truy xuất tài liệu trong notebook để trả lời

Chỉ trả về đúng 1 nhãn.

Gợi ý: Nếu câu hỏi chứa chi tiết cần trích dẫn/tài liệu, hoặc hỏi về nội dung file/chunk/khái niệm trong notebook -> retrieval_needed.

Lịch sử user gần nhất (nếu có): {last_user}
Tin nhắn hiện tại: {query}"""

        try:
            resp = await self.llm.chat(
                [{"role": "system", "content": "Bạn phân loại routing."}, {"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=20,
            )
            label = (resp or "").strip().lower()
            for candidate in ["greeting", "chitchat", "meta", "out_of_scope", "retrieval_needed"]:
                if candidate in label:
                    return {"route": candidate, "confidence": 0.7}
        except Exception as e:
            logger.warning(f"[router] LLM classify failed: {e}")

        return {"route": "retrieval_needed", "confidence": 0.5}

