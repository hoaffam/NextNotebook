"""
Custom Exceptions
Application-specific exceptions
"""


class NotebookLMException(Exception):
    """Base exception for NotebookLM application"""
    pass


class DocumentProcessingError(NotebookLMException):
    """Error during document processing"""
    pass


class EmbeddingError(NotebookLMException):
    """Error during embedding generation"""
    pass


class VectorDBError(NotebookLMException):
    """Error with vector database operations"""
    pass


class LLMError(NotebookLMException):
    """Error with LLM operations"""
    pass


class QuizGenerationError(NotebookLMException):
    """Error during quiz generation"""
    pass


class NotFoundError(NotebookLMException):
    """Resource not found"""
    pass


class ValidationError(NotebookLMException):
    """Validation error"""
    pass
