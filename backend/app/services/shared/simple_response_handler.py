"""
Simple Response Handler
Handles non-retrieval routes (greeting, chitchat, meta, out_of_scope) without RAG.
"""

from __future__ import annotations

from typing import List, Optional


class SimpleResponseHandler:
    def __init__(self, llm_service=None):
        self.llm = llm_service

    async def handle_greeting(self, query: str) -> str:
        # Template is enough; no LLM needed.
        return "Chào bạn! Bạn muốn hỏi gì về tài liệu trong notebook của mình?"

    async def handle_chitchat(self, query: str, chat_history: Optional[List] = None) -> str:
        # Lightweight LLM response; if no LLM, use a template.
        if not self.llm:
            return "Mình đây. Bạn có thể hỏi mình về nội dung tài liệu trong notebook nhé."

        messages = [{"role": "system", "content": "Bạn trò chuyện ngắn gọn, thân thiện, không cần truy xuất tài liệu."}]
        if chat_history:
            for msg in chat_history[-5:]:
                if hasattr(msg, "role"):
                    messages.append({"role": msg.role, "content": msg.content})
                else:
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": query})
        return await self.llm.chat(messages, temperature=0.7, max_tokens=300)

    async def handle_meta(self, query: str, notebook_name: str = None) -> str:
        name = f" '{notebook_name}'" if notebook_name else ""
        return (
            "Mình có thể giúp bạn tra cứu và trả lời dựa trên nội dung tài liệu trong notebook"
            f"{name}, kèm trích dẫn.\n"
            "- Hỏi về khái niệm/định nghĩa trong tài liệu\n"
            "- Tóm tắt phần nội dung\n"
            "- Tạo quiz/FAQ bằng lệnh /quiz, /summary, /faq\n"
            "Bạn hãy đặt câu hỏi cụ thể về tài liệu nhé."
        )

    async def handle_out_of_scope(self, query: str) -> str:
        return (
            "Mình chưa chắc câu hỏi này liên quan tới tài liệu trong notebook.\n"
            "Bạn có thể:\n"
            "- Hỏi lại theo hướng bám sát nội dung tài liệu (tên chương/mục/khái niệm)\n"
            "- Hoặc cung cấp thêm ngữ cảnh bạn muốn đối chiếu trong notebook"
        )

