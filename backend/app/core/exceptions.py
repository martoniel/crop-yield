"""
app/core/exceptions.py
──────────────────────
Custom exception classes for the CropYieldAI backend.
Keeps error handling consistent and API responses descriptive.
"""


class CropAIBaseException(Exception):
    """Base exception for all application-specific errors."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail or message
        super().__init__(self.message)


class ModelNotLoadedError(CropAIBaseException):
    """Raised when the ML model artifacts are not loaded or accessible."""


class PredictionError(CropAIBaseException):
    """Raised when the model fails to produce a prediction."""


class PreprocessingError(CropAIBaseException):
    """Raised when input data cannot be preprocessed correctly."""


class InvalidInputError(CropAIBaseException):
    """Raised when the input data fails domain-level validation."""


class RecordNotFoundError(CropAIBaseException):
    """Raised when a requested database record does not exist."""


class DatabaseError(CropAIBaseException):
    """Raised when a database operation fails unexpectedly."""


class AuthenticationError(CropAIBaseException):
    """Raised on invalid credentials or expired tokens."""


class AuthorizationError(CropAIBaseException):
    """Raised when a user attempts an action they are not permitted to perform."""
