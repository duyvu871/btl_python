from pydantic import BaseModel, Field
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    """
    Structure for SUCCESS responses (2xx).
    """
    success: bool = Field(default=True)
    message: Optional[str] = Field(default=None)
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    """
    Structure for ERROR responses (4xx, 5xx).
    """
    success: bool = Field(default=False)
    error_code: str = "ERROR"
    message: str