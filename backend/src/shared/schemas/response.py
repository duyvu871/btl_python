from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')

class SuccessResponse[T](BaseModel):
    """
    Structure for SUCCESS responses (2xx).
    """
    success: bool = Field(default=True)
    message: str | None = Field(default=None)
    data: T | None = None

class ErrorResponse(BaseModel):
    """
    Structure for ERROR responses (4xx, 5xx).
    """
    success: bool = Field(default=False)
    error_code: str = Field(default="ERROR")
    message: str
    data: Any | None = None
