"""AI文化知识问答HTTP路由。"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.response import ApiResponse, success
from app.schemas.ai import (
    AIChatData,
    AIChatRequest,
    AIChatSource,
    CreationSuggestionRead,
)
from app.services.ai.creation_suggestion import build_creation_suggestion
from app.services.ai.dependencies import get_rag_service
from app.services.ai.rag_service import RAGService


router = APIRouter(prefix="/ai", tags=["AI"])


@router.post(
    "/chat",
    response_model=ApiResponse[AIChatData],
    summary="岭南文化RAG知识问答",
)
async def chat(
    payload: AIChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> dict:
    result = await rag_service.answer(payload.question)
    suggestion = build_creation_suggestion(result)
    data = AIChatData(
        answer=result.answer,
        sources=[
            AIChatSource(
                source_path=source.source_path,
                title=source.title,
                section=source.section,
                score=source.score,
            )
            for source in result.sources
        ],
        creation_suggestion=CreationSuggestionRead(
            enable=suggestion.enable,
            culture=suggestion.culture,
            campus=suggestion.campus,
            style=suggestion.style,
        ),
    )
    return success(data.model_dump())
