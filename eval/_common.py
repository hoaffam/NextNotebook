"""
Eval common utilities (dataset loading, normalization, stable IDs).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def ensure_backend_on_path() -> None:
    """
    Ensure `backend/` is on sys.path so we can import `app.*` from eval scripts.
    """
    root = Path(__file__).resolve().parents[1]
    backend_dir = root / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def stable_doc_id_from_url(url: str) -> str:
    """
    Milvus schema uses document_id max_length=128.
    URLs can exceed this; use a stable hash-based ID.
    """
    u = (url or "").strip()
    h = hashlib.sha1(u.encode("utf-8")).hexdigest()  # 40 chars
    return f"urlsha1_{h}"


_re_ws = re.compile(r"\s+")
_re_punct = re.compile(r"[^\w\s]", re.UNICODE)


def normalize_text(s: str, drop_punct: bool = True) -> str:
    """
    Normalize for robust substring matching against chunk text.
    - lower
    - normalize unicode dashes to '-'
    - collapse whitespace
    - optional punctuation stripping
    """
    if not s:
        return ""
    s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u00a0", " ")
    s = s.lower()
    if drop_punct:
        s = _re_punct.sub(" ", s)
    s = _re_ws.sub(" ", s).strip()
    return s


def safe_first(value: Optional[str], n: int = 120) -> str:
    s = value or ""
    s = s.replace("\n", " ").strip()
    return s[:n]

