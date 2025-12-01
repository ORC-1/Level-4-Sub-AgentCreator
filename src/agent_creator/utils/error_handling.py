"""
Custom exceptions for Gemini API interactions
"""

class GeminiAPIError(Exception):
    """Base exception for Gemini API errors"""
    pass


class RateLimitError(GeminiAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class QuotaExceededError(GeminiAPIError):
    """Raised when API quota is exhausted"""
    pass


class InvalidAPIKeyError(GeminiAPIError):
    """Raised when API key is invalid or missing"""
    pass


class SafetyFilterError(GeminiAPIError):
    """Raised when content is blocked by safety filters"""
    pass