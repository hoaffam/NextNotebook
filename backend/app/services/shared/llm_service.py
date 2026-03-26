"""
Multi-provider LLM Service
Supports Groq (FREE), xAI (Grok), Google Gemini, and OpenAI
"""

from typing import List, Dict, Optional
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize provider-specific clients
_openai_client = None
_groq_client = None
_gemini_model = None

if settings.LLM_PROVIDER == "groq":
    from groq import Groq
    _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    logger.info(f"Initialized Groq client with model: {settings.GROQ_MODEL}")
elif settings.LLM_PROVIDER in ["xai", "openai"]:
    from openai import OpenAI
    if settings.LLM_PROVIDER == "xai":
        _openai_client = OpenAI(
            api_key=settings.XAI_API_KEY,
            base_url=settings.XAI_BASE_URL
        )
        logger.info(f"Initialized xAI client with model: {settings.XAI_MODEL}")
    else:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info(f"Initialized OpenAI client with model: {settings.OPENAI_MODEL}")
elif settings.LLM_PROVIDER == "gemini":
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    _gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
    logger.info(f"Initialized Gemini client with model: {settings.GEMINI_MODEL}")


class LLMService:
    """Multi-provider LLM service"""

    def __init__(self):
        """Initialize LLM client based on provider setting"""
        self.provider = settings.LLM_PROVIDER
        self.openai_client = _openai_client
        self.groq_client = _groq_client
        self.gemini_model = _gemini_model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate a chat response using the configured provider

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text
        """
        try:
            if self.provider == "groq":
                return await self._chat_groq(messages, temperature, max_tokens)
            elif self.provider in ["xai", "openai"]:
                return await self._chat_openai_compatible(messages, temperature, max_tokens)
            elif self.provider == "gemini":
                return await self._chat_gemini(messages, temperature, max_tokens)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            raise

    async def _chat_groq(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Chat using Groq API (FREE tier)"""
        response = self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def _chat_openai_compatible(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Chat using OpenAI-compatible API (xAI, OpenAI)"""
        model_name = settings.XAI_MODEL if self.provider == "xai" else settings.OPENAI_MODEL

        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    async def _chat_gemini(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Chat using Gemini API"""
        import google.generativeai as genai

        # Convert messages to Gemini format
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if role == 'system':
                system_instruction = content
            elif role == 'assistant':
                gemini_messages.append({
                    'role': 'model',
                    'parts': [content]
                })
            else:  # user
                gemini_messages.append({
                    'role': 'user',
                    'parts': [content]
                })

        # Create model with system instruction if provided
        if system_instruction:
            model = genai.GenerativeModel(
                settings.GEMINI_MODEL,
                system_instruction=system_instruction
            )
        else:
            model = self.gemini_model

        # Generate response
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )

        if gemini_messages:
            chat = model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
            response = chat.send_message(
                gemini_messages[-1]['parts'][0] if gemini_messages else "",
                generation_config=generation_config
            )
        else:
            response = model.generate_content(
                "Hello",
                generation_config=generation_config
            )

        return response.text

    async def generate_answer_without_citations(
        self,
        question: str,
        context: str,
        chat_history: List[Dict] = None,
        language: str = "Vietnamese"
    ) -> str:
        """
        Step 1 of 3-step citation flow: Generate natural answer without citations
        LLM focuses purely on content quality
        
        Args:
            question: User question
            context: Document context
            chat_history: Previous conversation messages
            language: Response language
            
        Returns:
            Natural answer without any [cid:X] markers
        """
        system_prompt = f"""Bạn là trợ lý AI thông minh, trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.

QUY TẮC:
- Trả lời rõ ràng, tự nhiên, dễ hiểu
- Chỉ dùng thông tin từ ngữ cảnh
- Nếu không đủ thông tin, nói rõ
- KHÔNG thêm bất kỳ citation nào (không dùng [cid:x], [1], [2], v.v.)

Ngữ cảnh:
{context}"""

        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            for msg in chat_history[-5:]:
                if hasattr(msg, 'role'):
                    messages.append({"role": msg.role, "content": msg.content})
                else:
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        messages.append({"role": "user", "content": question})
        
        return await self.chat(messages, temperature=0.7, max_tokens=2000)

    async def add_citations_to_answer(
        self,
        base_answer: str,
        citation_catalog: str
    ) -> str:
        """
        Step 2 of 3-step citation flow: Add inline citations [cid:x] to existing answer
        LLM focuses purely on accurate citation placement
        
        Args:
            base_answer: Answer text without citations
            citation_catalog: Formatted catalog of available citations
            
        Returns:
            Answer with [cid:X] markers added
        """
        system_prompt = f"""Bạn là chuyên gia thêm trích dẫn (citations) vào câu trả lời.

NHIỆM VỤ:
- Đọc câu trả lời và danh sách citation catalog
- Thêm [cid:X] ngay sau mỗi câu/thông tin lấy từ nguồn tương ứng
- KHÔNG thay đổi nội dung câu trả lời
- KHÔNG thêm hoặc bớt thông tin

QUY TẮC CITATION:
- Dùng đúng cú pháp: [cid:1], [cid:2], v.v.
- Chỉ dùng các cid có trong catalog (KHÔNG bịa số)
- Đặt [cid:X] ngay sau câu/mệnh đề lấy từ nguồn đó
- Có thể dùng nhiều citation cho một câu: [cid:2][cid:5]
- Mỗi mệnh đề quan trọng nên có ít nhất 1 citation

CITATION CATALOG (các nguồn được phép):
{citation_catalog if citation_catalog else '(Không có citation)'}"""

        prompt = f"""Câu trả lời cần thêm citation:

{base_answer}

---
Hãy trả về câu trả lời đã được thêm [cid:X] ở các vị trí phù hợp.
KHÔNG thay đổi nội dung, CHỈ thêm [cid:X]."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        return await self.chat(messages, temperature=0.2, max_tokens=2500)

    async def summarize(
        self,
        text: str,
        style: str = "detailed",
        max_length: int = None
    ) -> str:
        """Summarize text content"""
        style_prompts = {
            "brief": "Tóm tắt ngắn gọn trong 2-3 câu.",
            "detailed": "Tóm tắt chi tiết, bao gồm các điểm chính.",
            "bullet_points": "Tóm tắt dạng danh sách các điểm chính."
        }

        style_instruction = style_prompts.get(style, style_prompts["detailed"])

        prompt = f"""Hãy tóm tắt nội dung sau đây bằng tiếng Việt.

{style_instruction}

Nội dung:
{text[:15000]}"""

        messages = [
            {"role": "system", "content": "Bạn là chuyên gia tóm tắt tài liệu."},
            {"role": "user", "content": prompt}
        ]

        return await self.chat(messages, temperature=0.5, max_tokens=max_length or 1500)

    async def generate_questions(
        self,
        text: str,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """Generate quiz questions from text"""
        difficulty_prompts = {
            "easy": "câu hỏi đơn giản, dễ trả lời",
            "medium": "câu hỏi trung bình, cần hiểu nội dung",
            "hard": "câu hỏi khó, cần phân tích sâu"
        }

        diff_instruction = difficulty_prompts.get(difficulty, difficulty_prompts["medium"])

        prompt = f"""Dựa trên nội dung sau, tạo {num_questions} câu hỏi trắc nghiệm ({diff_instruction}).

Mỗi câu hỏi cần có:
- question: Nội dung câu hỏi
- options: 4 lựa chọn A, B, C, D
- correct_answer: Đáp án đúng (A, B, C, hoặc D)
- explanation: Giải thích tại sao đáp án đúng

Trả về dạng JSON array:
[
  {{
    "question": "Câu hỏi?",
    "options": ["A. X", "B. Y", "C. Z", "D. W"],
    "correct_answer": "A",
    "explanation": "Giải thích..."
  }}
]

Nội dung:
{text[:10000]}"""

        messages = [
            {"role": "system", "content": "Bạn là chuyên gia tạo câu hỏi trắc nghiệm. Chỉ trả về JSON hợp lệ."},
            {"role": "user", "content": prompt}
        ]

        response = await self.chat(messages, temperature=0.7, max_tokens=3000)

        try:
            import json
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
            return []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse quiz JSON: {response}")
            return []

    async def grade_documents(
        self,
        question: str,
        documents: List[str]
    ) -> List[float]:
        """
        Grade relevance scores in [0,1] for each document (0 = không liên quan, 1 = rất liên quan)
        """
        import re
        
        prompt = f"""Đánh giá mức độ liên quan của các đoạn văn với câu hỏi, cho điểm từ 0 đến 1.
0 = không liên quan, 1 = rất liên quan.
Trả lời theo định dạng: 1:0.82, 2:0.15, 3:0.67 ...

Câu hỏi: {question}

Các đoạn:
"""
        for i, doc in enumerate(documents):
            max_chars = min(int(len(doc) * 1.1), 2000)  # cắt động theo độ dài chunk, trần 2000
            prompt += f"\nĐoạn {i+1}:\n{doc[:max_chars]}\n"

        prompt += "\nHãy trả lời đúng định dạng: 1:0.xx, 2:0.xx, ..."

        messages = [
            {"role": "system", "content": "Bạn đánh giá độ liên quan của tài liệu và cho điểm từ 0 đến 1."},
            {"role": "user", "content": prompt}
        ]

        response = await self.chat(messages, temperature=0.3, max_tokens=200)
        # Parse scores
        scores = [0.0] * len(documents)
        try:
            matches = re.findall(r"(\d+)\s*[:=]\s*([0-9]*\.?[0-9]+)", response)
            logger.info(f"Matches: {matches}")
            for idx_str, val_str in matches:
                idx = int(idx_str) - 1
                if 0 <= idx < len(scores):
                    val = float(val_str)
                    scores[idx] = max(0.0, min(1.0, val))
                    logger.info(f"Document {idx+1} relevance score: {scores[idx]:.3f}")
        except Exception:
            pass

        return scores

    async def rewrite_query(self, original_query: str) -> str:
        """Rewrite a query to be more effective for retrieval"""
        prompt = f"""Viết lại câu hỏi sau thành một câu tìm kiếm ngắn gọn (tối đa 100 từ).
Chỉ trả về câu hỏi viết lại, không giải thích.

Câu hỏi gốc: {original_query}

Câu hỏi viết lại:"""

        messages = [
            {"role": "system", "content": "Bạn là chuyên gia tối ưu câu hỏi tìm kiếm. Chỉ trả về câu hỏi viết lại ngắn gọn."},
            {"role": "user", "content": prompt}
        ]

        result = await self.chat(messages, temperature=0.3, max_tokens=100)
        # Ensure result is not too long
        if len(result) > 300:
            return original_query  # Fallback to original if rewrite is too long
        return result.strip()

    async def generate_quiz(self, content: str, num_questions: int = 5) -> str:
        """Generate quiz questions as formatted text for chat display"""
        prompt = f"""Dựa trên nội dung tài liệu sau, hãy tạo {num_questions} câu hỏi trắc nghiệm.

Format mỗi câu hỏi như sau:
**Câu 1:** [Nội dung câu hỏi]
A. [Đáp án A]
B. [Đáp án B]
C. [Đáp án C]
D. [Đáp án D]

✅ **Đáp án:** [Đáp án đúng]
📖 **Giải thích:** [Giải thích ngắn gọn]

---

Nội dung tài liệu:
{content[:8000]}

Hãy tạo {num_questions} câu hỏi đa dạng, bao quát nội dung chính của tài liệu."""

        messages = [
            {"role": "system", "content": "Bạn là chuyên gia tạo câu hỏi trắc nghiệm giáo dục. Tạo câu hỏi rõ ràng, chính xác và có giá trị học tập."},
            {"role": "user", "content": prompt}
        ]

        response = await self.chat(messages, temperature=0.7, max_tokens=3000)
        return f"🎯 **Quiz - {num_questions} câu hỏi**\n\n{response}"

    async def generate_faq(self, content: str, num_questions: int = 5) -> str:
        """Generate FAQ from content"""
        prompt = f"""Dựa trên nội dung tài liệu sau, hãy tạo {num_questions} câu hỏi thường gặp (FAQ) và câu trả lời.

Format:
**Q: [Câu hỏi]**
**A:** [Câu trả lời chi tiết]

---

Nội dung tài liệu:
{content[:8000]}

Hãy tạo {num_questions} câu hỏi FAQ quan trọng nhất mà người đọc thường thắc mắc."""

        messages = [
            {"role": "system", "content": "Bạn là chuyên gia tạo FAQ. Tạo câu hỏi và trả lời rõ ràng, hữu ích."},
            {"role": "user", "content": prompt}
        ]

        response = await self.chat(messages, temperature=0.7, max_tokens=2000)
        return f"❓ **FAQ - {num_questions} câu hỏi thường gặp**\n\n{response}"


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get singleton LLMService instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
