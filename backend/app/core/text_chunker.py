"""
Text Chunker
Split text into chunks for embedding and retrieval
Supports file-type-specific chunking strategies (PDF, DOCX, TXT)
"""

from typing import List, Dict, Optional, Any
import re
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TextChunker:
    """
    Intelligent text chunking with overlap
    
    Uses recursive character splitting strategy:
    1. Try to split by paragraphs
    2. If too large, split by sentences
    3. If still too large, split by words
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        
    def chunk_text(self, text: str) -> List[Dict]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Clean text first
        text = self._clean_text(text)
        
        if not text:
            return []
        
        # Split using recursive strategy
        chunks = self._recursive_split(text)
        
        # Add metadata to chunks
        result = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                result.append({
                    "text": chunk.strip(),
                    "chunk_index": i,
                    "char_count": len(chunk),
                    "word_count": len(chunk.split())
                })
        
        logger.info(f"Created {len(result)} chunks from {len(text)} characters")
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text
    
    def _recursive_split(
        self, 
        text: str, 
        separators: List[str] = None
    ) -> List[str]:
        """Recursively split text using different separators"""
        if separators is None:
            separators = self.separators.copy()
        
        # Base case: text is small enough
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        
        # No more separators to try
        if not separators:
            return self._split_by_size(text)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        # Split by current separator
        if separator:
            splits = text.split(separator)
        else:
            # Empty separator means split by character
            return self._split_by_size(text)
        
        # Merge splits into chunks
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = len(split)
            
            # If single split is too large, recursively split it
            if split_length > self.chunk_size:
                # First, add current chunk if any
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Recursively split the large piece
                sub_chunks = self._recursive_split(split, remaining_separators)
                chunks.extend(sub_chunks)
                continue
            
            # Check if adding this split would exceed chunk size
            new_length = current_length + split_length + len(separator)
            
            if new_length > self.chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append(separator.join(current_chunk))
                
                # Keep overlap from end of current chunk
                overlap_text = self._get_overlap_text(current_chunk, separator)
                
                if overlap_text:
                    current_chunk = [overlap_text, split]
                    current_length = len(overlap_text) + split_length + len(separator)
                else:
                    current_chunk = [split]
                    current_length = split_length
            else:
                current_chunk.append(split)
                current_length = new_length
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(separator.join(current_chunk))
        
        return chunks
    
    def _split_by_size(self, text: str) -> List[str]:
        """Split text by fixed size as last resort"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to find a good break point
            if end < len(text):
                # Look for space near the end
                space_pos = text.rfind(" ", start, end)
                if space_pos > start:
                    end = space_pos + 1
            
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        
        return chunks
    
    def _get_overlap_text(
        self, 
        chunk_parts: List[str], 
        separator: str
    ) -> Optional[str]:
        """Get overlap text from end of chunk"""
        if not chunk_parts:
            return None
        
        full_text = separator.join(chunk_parts)
        
        if len(full_text) <= self.chunk_overlap:
            return full_text
        
        # Get last N characters
        overlap = full_text[-self.chunk_overlap:]
        
        # Try to start at a word boundary
        space_pos = overlap.find(" ")
        if space_pos > 0:
            overlap = overlap[space_pos + 1:]
        
        return overlap if overlap.strip() else None
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Average ~4 characters per token for English
        # Vietnamese might be different
        return len(text) // 4

    # ============================================================
    # FILE-TYPE-SPECIFIC CHUNKING STRATEGIES
    # ============================================================

    def chunk_pdf(self, pages_data: List[Dict]) -> List[Dict]:
        """
        Chunk PDF with page-aware strategy

        Args:
            pages_data: List of page dictionaries with structure:
                {
                    "page_number": int,
                    "text": str,
                    "char_start": int,  # Global position in document
                    "char_end": int
                }

        Returns:
            List of chunks with enhanced metadata including page numbers
        """
        chunks = []
        chunk_index = 0

        for page_data in pages_data:
            page_num = page_data["page_number"]
            page_text = page_data["text"]
            page_char_start = page_data["char_start"]

            # Split page text into paragraphs (by double newline)
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]

            current_chunk = []
            current_length = 0
            para_index = 0
            chunk_start_para = 0
            chunk_char_start = page_char_start

            for para in paragraphs:
                para_length = len(para)

                # If single paragraph exceeds chunk size, split it
                if para_length > self.chunk_size:
                    # Save current chunk if any
                    if current_chunk:
                        chunk_text = "\n\n".join(current_chunk)
                        chunks.append(self._create_pdf_chunk(
                            text=chunk_text,
                            chunk_index=chunk_index,
                            page_number=page_num,
                            paragraph_start=chunk_start_para,
                            paragraph_end=para_index - 1,
                            char_start=chunk_char_start,
                            char_end=chunk_char_start + len(chunk_text)
                        ))
                        chunk_index += 1
                        current_chunk = []
                        current_length = 0

                    # Split large paragraph into sentences
                    sub_chunks = self._split_by_sentences(para, self.chunk_size)
                    for sub_chunk in sub_chunks:
                        chunks.append(self._create_pdf_chunk(
                            text=sub_chunk,
                            chunk_index=chunk_index,
                            page_number=page_num,
                            paragraph_start=para_index,
                            paragraph_end=para_index,
                            char_start=chunk_char_start,
                            char_end=chunk_char_start + len(sub_chunk)
                        ))
                        chunk_index += 1
                        chunk_char_start += len(sub_chunk)

                    para_index += 1
                    continue

                # Check if adding paragraph exceeds chunk size
                new_length = current_length + para_length + 2  # +2 for \n\n

                if new_length > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(self._create_pdf_chunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        page_number=page_num,
                        paragraph_start=chunk_start_para,
                        paragraph_end=para_index - 1,
                        char_start=chunk_char_start,
                        char_end=chunk_char_start + len(chunk_text)
                    ))
                    chunk_index += 1

                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk, "\n\n")
                    if overlap_text:
                        current_chunk = [overlap_text, para]
                        current_length = len(overlap_text) + para_length + 2
                        chunk_char_start = chunk_char_start + len(chunk_text) - len(overlap_text)
                    else:
                        current_chunk = [para]
                        current_length = para_length
                        chunk_char_start = chunk_char_start + len(chunk_text)

                    chunk_start_para = para_index
                else:
                    # Add paragraph to current chunk
                    current_chunk.append(para)
                    current_length = new_length

                para_index += 1

            # Save remaining chunk from this page
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(self._create_pdf_chunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    page_number=page_num,
                    paragraph_start=chunk_start_para,
                    paragraph_end=para_index - 1,
                    char_start=chunk_char_start,
                    char_end=chunk_char_start + len(chunk_text)
                ))
                chunk_index += 1

        logger.info(f"Created {len(chunks)} chunks from {len(pages_data)} PDF pages")
        return chunks

    def chunk_docx(self, sections_data: List[Dict]) -> List[Dict]:
        """
        Chunk DOCX with heading-aware strategy

        Args:
            sections_data: List of section dictionaries with structure:
                {
                    "heading": str,
                    "heading_level": int,  # 1, 2, 3...
                    "paragraphs": List[str],
                    "char_start": int,
                    "char_end": int,
                    "section_path": str,  # "Chapter 1 > Introduction"
                    "tables": List[Dict]  # Optional table data
                }

        Returns:
            List of chunks with heading hierarchy metadata
        """
        chunks = []
        chunk_index = 0

        for section in sections_data:
            heading = section.get("heading", "")
            heading_level = section.get("heading_level", 1)
            section_path = section.get("section_path", heading)
            paragraphs = section.get("paragraphs", [])
            tables = section.get("tables", [])
            char_start = section.get("char_start", 0)

            # Chunk paragraphs within section
            current_chunk = []
            current_length = 0
            para_index = 0
            chunk_start_para = 0
            chunk_char_start = char_start

            for para in paragraphs:
                para_length = len(para)

                # If paragraph too large, split it
                if para_length > self.chunk_size:
                    # Save current chunk
                    if current_chunk:
                        chunk_text = "\n\n".join(current_chunk)
                        chunks.append(self._create_docx_chunk(
                            text=chunk_text,
                            chunk_index=chunk_index,
                            heading=heading,
                            heading_level=heading_level,
                            section_path=section_path,
                            paragraph_start=chunk_start_para,
                            paragraph_end=para_index - 1,
                            char_start=chunk_char_start,
                            char_end=chunk_char_start + len(chunk_text)
                        ))
                        chunk_index += 1
                        current_chunk = []
                        current_length = 0

                    # Split large paragraph
                    sub_chunks = self._split_by_sentences(para, self.chunk_size)
                    for sub_chunk in sub_chunks:
                        chunks.append(self._create_docx_chunk(
                            text=sub_chunk,
                            chunk_index=chunk_index,
                            heading=heading,
                            heading_level=heading_level,
                            section_path=section_path,
                            paragraph_start=para_index,
                            paragraph_end=para_index,
                            char_start=chunk_char_start,
                            char_end=chunk_char_start + len(sub_chunk)
                        ))
                        chunk_index += 1
                        chunk_char_start += len(sub_chunk)

                    para_index += 1
                    continue

                # Check if adding paragraph exceeds size
                new_length = current_length + para_length + 2

                if new_length > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(self._create_docx_chunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        heading=heading,
                        heading_level=heading_level,
                        section_path=section_path,
                        paragraph_start=chunk_start_para,
                        paragraph_end=para_index - 1,
                        char_start=chunk_char_start,
                        char_end=chunk_char_start + len(chunk_text)
                    ))
                    chunk_index += 1

                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk, "\n\n")
                    if overlap_text:
                        current_chunk = [overlap_text, para]
                        current_length = len(overlap_text) + para_length + 2
                    else:
                        current_chunk = [para]
                        current_length = para_length

                    chunk_start_para = para_index
                else:
                    current_chunk.append(para)
                    current_length = new_length

                para_index += 1

            # Save remaining paragraphs
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(self._create_docx_chunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    heading=heading,
                    heading_level=heading_level,
                    section_path=section_path,
                    paragraph_start=chunk_start_para,
                    paragraph_end=para_index - 1,
                    char_start=chunk_char_start,
                    char_end=chunk_char_start + len(chunk_text)
                ))
                chunk_index += 1

            # Handle tables separately
            for table in tables:
                table_text = table.get("text", "")
                if table_text:
                    chunks.append(self._create_docx_chunk(
                        text=table_text,
                        chunk_index=chunk_index,
                        heading=heading,
                        heading_level=heading_level,
                        section_path=section_path,
                        paragraph_start=-1,  # Indicate it's a table
                        paragraph_end=-1,
                        char_start=table.get("char_start", 0),
                        char_end=table.get("char_end", 0),
                        table_name=table.get("name", "Table")
                    ))
                    chunk_index += 1

        logger.info(f"Created {len(chunks)} chunks from {len(sections_data)} DOCX sections")
        return chunks

    def chunk_txt(self, text: str, line_tracking: bool = True) -> List[Dict]:
        """
        Chunk TXT with line-number tracking

        Args:
            text: Full text content
            line_tracking: Whether to track line numbers

        Returns:
            List of chunks with line number metadata
        """
        chunks = []

        if not line_tracking:
            # Fallback to regular chunking
            return self.chunk_text(text)

        # Split into lines for tracking
        lines = text.split("\n")

        # Group into paragraphs (separated by blank lines)
        paragraphs = []
        current_para_lines = []
        current_para_start_line = 1

        for line_num, line in enumerate(lines, start=1):
            if line.strip():
                current_para_lines.append(line)
            else:
                # Blank line - end of paragraph
                if current_para_lines:
                    paragraphs.append({
                        "text": "\n".join(current_para_lines),
                        "line_start": current_para_start_line,
                        "line_end": line_num - 1,
                        "paragraph_number": len(paragraphs) + 1
                    })
                    current_para_lines = []
                    current_para_start_line = line_num + 1

        # Don't forget last paragraph
        if current_para_lines:
            paragraphs.append({
                "text": "\n".join(current_para_lines),
                "line_start": current_para_start_line,
                "line_end": len(lines),
                "paragraph_number": len(paragraphs) + 1
            })

        # Now chunk the paragraphs
        chunk_index = 0
        current_chunk_paras = []
        current_length = 0

        for para in paragraphs:
            para_text = para["text"]
            para_length = len(para_text)

            # If single paragraph is too large, split it
            if para_length > self.chunk_size:
                # Save current chunk
                if current_chunk_paras:
                    chunks.append(self._create_txt_chunk(
                        paragraphs=current_chunk_paras,
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
                    current_chunk_paras = []
                    current_length = 0

                # Split large paragraph
                sub_chunks = self._split_by_sentences(para_text, self.chunk_size)
                for sub_chunk in sub_chunks:
                    chunks.append({
                        "text": sub_chunk,
                        "chunk_index": chunk_index,
                        "file_type": "txt",
                        "line_start": para["line_start"],
                        "line_end": para["line_end"],
                        "paragraph_number": para["paragraph_number"],
                        "char_count": len(sub_chunk),
                        "word_count": len(sub_chunk.split())
                    })
                    chunk_index += 1
                continue

            # Check if adding paragraph exceeds size
            new_length = current_length + para_length + 2

            if new_length > self.chunk_size and current_chunk_paras:
                # Save current chunk
                chunks.append(self._create_txt_chunk(
                    paragraphs=current_chunk_paras,
                    chunk_index=chunk_index
                ))
                chunk_index += 1

                # Start new chunk (with overlap would be complex for line tracking)
                current_chunk_paras = [para]
                current_length = para_length
            else:
                current_chunk_paras.append(para)
                current_length = new_length

        # Save remaining chunk
        if current_chunk_paras:
            chunks.append(self._create_txt_chunk(
                paragraphs=current_chunk_paras,
                chunk_index=chunk_index
            ))

        logger.info(f"Created {len(chunks)} chunks from TXT with line tracking")
        return chunks

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def _split_by_sentences(self, text: str, max_size: int) -> List[str]:
        """Split text by sentences when paragraph is too large"""
        # Simple sentence splitting by common punctuation
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if sentence_length > max_size:
                # Even single sentence is too large, force split
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # Force split by size
                chunks.extend(self._split_by_size(sentence))
                continue

            if current_length + sentence_length > max_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 for space

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _create_pdf_chunk(
        self,
        text: str,
        chunk_index: int,
        page_number: int,
        paragraph_start: int,
        paragraph_end: int,
        char_start: int,
        char_end: int
    ) -> Dict:
        """Create PDF chunk with enhanced metadata"""
        return {
            "text": text,
            "chunk_index": chunk_index,
            "file_type": "pdf",
            "page_number": page_number,
            "paragraph_start": paragraph_start,
            "paragraph_end": paragraph_end,
            "char_start": char_start,
            "char_end": char_end,
            "char_count": len(text),
            "word_count": len(text.split())
        }

    def _create_docx_chunk(
        self,
        text: str,
        chunk_index: int,
        heading: str,
        heading_level: int,
        section_path: str,
        paragraph_start: int,
        paragraph_end: int,
        char_start: int,
        char_end: int,
        table_name: Optional[str] = None
    ) -> Dict:
        """Create DOCX chunk with heading metadata"""
        chunk = {
            "text": text,
            "chunk_index": chunk_index,
            "file_type": "docx",
            "heading": heading,
            "heading_level": heading_level,
            "section_path": section_path,
            "paragraph_start": paragraph_start,
            "paragraph_end": paragraph_end,
            "char_start": char_start,
            "char_end": char_end,
            "char_count": len(text),
            "word_count": len(text.split())
        }

        if table_name:
            chunk["table_name"] = table_name
            chunk["is_table"] = True

        return chunk

    def _create_txt_chunk(
        self,
        paragraphs: List[Dict],
        chunk_index: int
    ) -> Dict:
        """Create TXT chunk with line number metadata"""
        text = "\n\n".join([p["text"] for p in paragraphs])

        return {
            "text": text,
            "chunk_index": chunk_index,
            "file_type": "txt",
            "line_start": paragraphs[0]["line_start"],
            "line_end": paragraphs[-1]["line_end"],
            "paragraph_start": paragraphs[0]["paragraph_number"],
            "paragraph_end": paragraphs[-1]["paragraph_number"],
            "char_count": len(text),
            "word_count": len(text.split())
        }
