"""
Text Cleaner
Clean and preprocess text for better processing
"""

import re
from typing import Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TextCleaner:
    """Clean and normalize text content"""
    
    def __init__(self, language: str = "vi"):
        """
        Initialize text cleaner
        
        Args:
            language: Primary language ('vi' for Vietnamese, 'en' for English)
        """
        self.language = language
    
    def clean(self, text: str, options: dict = None) -> str:
        """
        Clean text with configurable options
        
        Args:
            text: Input text
            options: Cleaning options
                - remove_urls: Remove URLs (default: True)
                - remove_emails: Remove emails (default: True)
                - remove_extra_whitespace: Normalize whitespace (default: True)
                - remove_special_chars: Remove special characters (default: False)
                - lowercase: Convert to lowercase (default: False)
        """
        if not text:
            return ""
        
        options = options or {}
        
        # Default options
        remove_urls = options.get("remove_urls", True)
        remove_emails = options.get("remove_emails", True)
        remove_extra_whitespace = options.get("remove_extra_whitespace", True)
        remove_special_chars = options.get("remove_special_chars", False)
        lowercase = options.get("lowercase", False)
        
        result = text
        
        # Remove URLs
        if remove_urls:
            result = self._remove_urls(result)
        
        # Remove emails
        if remove_emails:
            result = self._remove_emails(result)
        
        # Remove special characters (but keep Vietnamese diacritics)
        if remove_special_chars:
            result = self._remove_special_chars(result)
        
        # Normalize whitespace
        if remove_extra_whitespace:
            result = self._normalize_whitespace(result)
        
        # Lowercase
        if lowercase:
            result = result.lower()
        
        return result.strip()
    
    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text"""
        url_pattern = r'https?://\S+|www\.\S+'
        return re.sub(url_pattern, '', text)
    
    def _remove_emails(self, text: str) -> str:
        """Remove email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, '', text)
    
    def _remove_special_chars(self, text: str) -> str:
        """
        Remove special characters while preserving:
        - Vietnamese diacritics
        - Basic punctuation
        - Numbers
        """
        # Keep Vietnamese characters, alphanumeric, and basic punctuation
        vietnamese_chars = (
            r'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
            r'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ'
        )
        pattern = f'[^a-zA-Z0-9{vietnamese_chars}\\s.,!?;:\\-]'
        return re.sub(pattern, '', text)
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace"""
        # Replace multiple spaces with single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text
    
    def remove_headers_footers(self, text: str) -> str:
        """
        Remove common header/footer patterns
        (Page numbers, headers, etc.)
        """
        # Remove page numbers like "Page 1", "Trang 1", "- 1 -"
        text = re.sub(r'(?i)(page|trang)\s*\d+', '', text)
        text = re.sub(r'-\s*\d+\s*-', '', text)
        
        # Remove common footer patterns
        text = re.sub(r'(?i)copyright.*?\n', '', text)
        text = re.sub(r'(?i)all rights reserved.*?\n', '', text)
        
        return text
    
    def extract_sentences(self, text: str) -> list:
        """Extract sentences from text"""
        # Simple sentence splitting
        # Works reasonably for both Vietnamese and English
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
