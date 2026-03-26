"""
Citation Policy & Validation
Handles citation prompt building and citation validation logic
"""

import re
from typing import Dict, Iterable, Set


def build_strict_citation_system_prompt(context: str, citation_catalog: str) -> str:
    """
    Build system prompt for STRICT citation enforcement (legacy single-step method)
    """
    return f"""Bạn là trợ lý AI trích dẫn nghiêm ngặt, trả lời dựa trên NGUỒN ĐƯỢC CUNG CẤP.

QUY TẮC BẮT BUỘC:
- Mỗi mệnh đề quan trọng phải có ít nhất 1 trích dẫn.
- Chỉ dùng các citation trong danh sách cho phép, với cú pháp [cid:ID] (ví dụ [cid:2]).
- Không được bịa hoặc đổi số ID. Không dùng các dạng [1], [2] tự nghĩ.
- Nếu thiếu thông tin để trích dẫn, hãy nói rõ và KHÔNG bịa cite.
- Khi tham chiếu nội dung, tuân thủ thứ tự và nhãn trong phần ngữ cảnh: mỗi đoạn có nhãn [chunk X | doc Y | file Z]. Giữ mạch logic theo thứ tự xuất hiện.

Cách chèn trích dẫn:
- Đặt [cid:X] ngay sau câu hoặc thông tin lấy từ nguồn đó.
- Có thể dùng nhiều cite cho một câu: [cid:2][cid:5].

Danh sách citation được phép (cid = citation_id):
{citation_catalog if citation_catalog else '(Không có citation nào được phép)'}

Ngữ cảnh:
{context}"""


def extract_used_citation_ids(answer: str) -> Set[int]:
    """
    Extract all [cid:X] markers from answer text
    
    Args:
        answer: Text containing [cid:X] markers
        
    Returns:
        Set of citation IDs used in answer
    """
    if not answer:
        return set()
    return set(int(m) for m in re.findall(r"\[cid:(\d+)\]", answer))


def validate_citations(answer: str, allowed_ids: Iterable[int]) -> Dict:
    """
    Validate citations in answer against allowed IDs
    
    Args:
        answer: Text containing [cid:X] markers
        allowed_ids: List/set of valid citation IDs
        
    Returns:
        Dict with validation results:
        - used_ids: List of valid citation IDs actually used
        - unknown_ids: List of invalid citation IDs used
        - has_unknown: Boolean flag for invalid citations
        - used_count: Count of valid citations used
    """
    allowed = set(int(x) for x in allowed_ids)
    used = extract_used_citation_ids(answer)
    unknown = sorted(list(used - allowed))
    used_known = sorted(list(used & allowed))
    
    return {
        "used_ids": used_known,
        "unknown_ids": unknown,
        "has_unknown": len(unknown) > 0,
        "used_count": len(used_known),
    }
