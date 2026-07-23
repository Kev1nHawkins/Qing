from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.context import request_id_context

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None
    request_id: str | None = Field(default=None, alias="requestId")

    model_config = {"populate_by_name": True}


def success(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "data": data,
        "requestId": request_id_context.get(),
    }
