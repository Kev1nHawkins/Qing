"""AI文化知识问答HTTP路由。"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.response import ApiResponse, success
from app.schemas.ai import (
    AIChatData,
    AIChatRequest,
    AIChatSource,
    CreationSuggestionRead,
    PostDraftData,
    PostDraftRequest,
)
from app.api.dependencies import CurrentUser
from app.services.ai.creation_suggestion import build_creation_suggestion
from app.services.ai.dependencies import get_rag_service
from app.services.ai.rag_service import RAGService
from app.services.ai.post_draft_service import PostDraftService


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
        mode=result.mode,
        provider=result.provider,
        model=result.model,
        fallback_used=result.fallback_used,
    )
    return success(data.model_dump(by_alias=True))


@router.post(
    "/post-drafts",
    response_model=ApiResponse[PostDraftData],
    summary="生成可编辑的社区推文草稿",
)
async def generate_post_draft(payload: PostDraftRequest, _: CurrentUser) -> dict:
    draft = await PostDraftService().generate(payload.prompt)
    data = PostDraftData(
        title=draft.title,
        content=draft.content,
        tags=draft.tags,
        provider=draft.provider,
        model=draft.model,
        fallbackUsed=draft.fallback_used,
    )
    return success(data.model_dump(by_alias=True), "推文草稿已生成")
