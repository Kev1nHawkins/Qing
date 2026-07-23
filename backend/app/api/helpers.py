from typing import Any, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


async def get_or_404(
    db: AsyncSession, model: type[ModelT], object_id: int, label: str = "记录"
) -> ModelT:
    obj = await db.get(model, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label}不存在")
    return obj


async def paginated(
    db: AsyncSession,
    *,
    stmt: Select[Any],
    count_stmt: Select[Any],
    page: int,
    page_size: int,
    schema: type[BaseModel],
) -> dict[str, Any]:
    total = int((await db.scalar(count_stmt)) or 0)
    rows = (await db.scalars(stmt.offset((page - 1) * page_size).limit(page_size))).all()
    return {
        "total": total,
        "items": [schema.model_validate(row).model_dump(by_alias=True) for row in rows],
        "page": page,
        "pageSize": page_size,
    }


def apply_changes(obj: Any, payload: BaseModel) -> None:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value.value if hasattr(value, "value") else value)

