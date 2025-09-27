from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    status: str  # "success" or "failed"
    data: Optional[T] = None
    error: Optional[str] = None

    @classmethod
    def success(cls, data: Any = None):
        return cls(status="success", data=data, error=None)
    
    @classmethod
    def failed(cls, error: str, data: Any = None):
        return cls(status="failed", data=data, error=error)
