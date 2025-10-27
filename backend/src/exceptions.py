# --- Base Class ---
class AppError(Exception):
    """Base class for all custom exceptions in this application."""
    pass

# --- Stage-specific errors ---
class RetrievalError(AppError):
    """Base class for errors that occur during the document retrieval process."""
    pass

class GenerationError(AppError):
    """Base class for errors that occur during the response generation process."""
    pass

# --- Errors categorized by nature and handling method (This is important!) ---
class RetryableRetrievalError(RetrievalError):
    """Retryable retrieval error (e.g., temporary network disconnection, API rate limit)."""
    pass

class NonRetryableRetrievalError(RetrievalError):
    """Retrieval error that will not succeed on retry (e.g., invalid API key, non-existent index)."""
    pass

# GenerationError can be extended in the same way
class RetryableGenerationError(GenerationError):
    """Retryable generation error (e.g., LLM is temporarily overloaded)."""
    pass

class NonRetryableGenerationError(GenerationError):
    """Generation error that will not succeed on retry (e.g., prompt violates policy)."""
    pass