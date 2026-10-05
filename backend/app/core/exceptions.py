"""
Custom application exceptions mapped to structured HTTP responses.
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with a structured detail payload."""

    def __init__(self, status_code: int, message: str, code: str = "APP_ERROR") -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, message, "NOT_FOUND")


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message, "VALIDATION_ERROR")


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, message, "UNAUTHORIZED")
