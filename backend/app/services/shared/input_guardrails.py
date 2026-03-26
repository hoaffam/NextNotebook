"""
Input Guardrails Service
Lightweight validation to prevent running retrieval for junk / unsafe inputs.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class InputGuardrailsService:
    def __init__(self, llm_service=None):
        self.llm = llm_service

        # Junk patterns
        self._re_many_repeats = re.compile(r"(.)\1{6,}")  # aaaaaaa, 1111111
        self._re_mostly_symbols = re.compile(r"^[\W_]{8,}$", re.UNICODE)

    async def validate_input(self, text: str) -> Dict:
        """
        Returns:
          - passed: bool
          - reason: str
          - severity: str (info|warning|block)
        """
        msg = (text or "").strip()

        # Basic checks
        if not msg:
            return {"passed": False, "reason": "Tin nhắn trống.", "severity": "info"}

        max_len = getattr(settings, "MAX_INPUT_LENGTH", 2000)
        min_len = getattr(settings, "MIN_INPUT_LENGTH", 2)
        if len(msg) < min_len:
            return {"passed": False, "reason": "Tin nhắn quá ngắn.", "severity": "info"}
        if len(msg) > max_len:
            return {"passed": False, "reason": f"Tin nhắn quá dài (>{max_len} ký tự).", "severity": "warning"}

        # Junk detection (rule-based)
        if self._is_junk(msg):
            return {"passed": False, "reason": "Tin nhắn có vẻ là spam/ký tự rác. Vui lòng nhập rõ hơn.", "severity": "info"}

        # Safety check (optional; only if enabled)
        if getattr(settings, "ENABLE_INPUT_SAFETY", True):
            safety = await self._check_safety_if_needed(msg)
            if safety and not safety.get("passed", True):
                return safety

        return {"passed": True, "reason": "", "severity": "info"}

    def _is_junk(self, msg: str) -> bool:
        # Too many repeated characters
        if self._re_many_repeats.search(msg):
            return True

        # Mostly symbols / punctuation
        if self._re_mostly_symbols.match(msg):
            return True

        # Very low alpha ratio (but allow code blocks/backticks)
        letters = sum(ch.isalpha() for ch in msg)
        digits = sum(ch.isdigit() for ch in msg)
        total = max(1, len(msg))
        if letters == 0 and digits == 0:
            return True
        if letters / total < 0.1 and ("```" not in msg):
            return True

        return False

    async def _check_safety_if_needed(self, msg: str) -> Optional[Dict]:
        """
        Lightweight LLM-based safety check for suspicious content.
        We only invoke LLM when suspicious keywords appear to avoid extra cost.
        """
        suspicious = any(
            kw in msg.lower()
            for kw in [
                "tự tử",
                "suicide",
                "kill",
                "bomb",
                "weapon",
                "hack",
                "porn",
                "sex",
            ]
        )
        if not suspicious:
            return None

        if not self.llm:
            # If no LLM available, do minimal blocking on very obvious cases
            if "tự tử" in msg.lower() or "suicide" in msg.lower():
                return {"passed": False, "reason": "Nội dung nhạy cảm. Vui lòng thay đổi câu hỏi.", "severity": "block"}
            return None

        prompt = f"""Bạn là bộ lọc an toàn nội dung. Hãy phân loại tin nhắn sau:
- SAFE: an toàn, có thể trả lời
- UNSAFE: bạo lực/hại bản thân/tình dục trẻ em/hướng dẫn phạm pháp

Chỉ trả về đúng 1 từ: SAFE hoặc UNSAFE.

Tin nhắn: {msg}"""

        try:
            resp = await self.llm.chat(
                [
                    {"role": "system", "content": "Bạn là bộ lọc an toàn nội dung."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=10,
            )
            verdict = (resp or "").strip().upper()
            if "UNSAFE" in verdict:
                return {"passed": False, "reason": "Nội dung không an toàn. Vui lòng thay đổi câu hỏi.", "severity": "block"}
        except Exception as e:
            logger.warning(f"[guardrails] safety check failed: {e}")

        return None

