from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, CurrentUser, DbSession
from app.api.helpers import apply_changes, get_or_404, paginated
from app.core.response import success
from app.models.creation import AICreation, CreationTemplate
from app.models.enums import CreationStatus
from app.schemas.creation import (
    CreationRead,
    CreationRequest,
    TemplateCreate,
    TemplateRead,
    TemplateUpdate,
)

router = APIRouter(prefix="/creations", tags=["Creation"])


@router.get("/templates", summary="AI 创作模板列表")
async def list_templates(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict:
    return success(
        await paginated(
            db,
            stmt=select(CreationTemplate).order_by(CreationTemplate.id),
            count_stmt=select(func.count(CreationTemplate.id)),
            page=page,
            page_size=page_size,
            schema=TemplateRead,
        )
    )


@router.post("/templates", status_code=201, summary="新增 AI 创作模板")
async def create_template(
    payload: TemplateCreate, db: DbSession, _: AdminUser
) -> dict:
    template = CreationTemplate(**payload.model_dump(mode="json"))
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return success(TemplateRead.model_validate(template).model_dump(), "创建成功")


@router.put("/templates/{template_id}", summary="更新 AI 创作模板")
async def update_template(
    template_id: int, payload: TemplateUpdate, db: DbSession, _: AdminUser
) -> dict:
    template = await get_or_404(db, CreationTemplate, template_id, "创作模板")
    apply_changes(template, payload)
    await db.commit()
    await db.refresh(template)
    return success(TemplateRead.model_validate(template).model_dump(), "更新成功")


@router.post("", status_code=202, summary="提交异步 AI 创作")
async def create_creation(
    payload: CreationRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    template = await get_or_404(db, CreationTemplate, payload.template_id, "创作模板")
    try:
        prompt = template.prompt_template.format(**payload.options)
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"缺少模板选项：{exc.args[0]}") from exc
    creation = AICreation(
        user_id=current_user.id,
        template_id=template.id,
        culture_item_id=payload.culture_item_id or template.culture_item_id,
        title=payload.title,
        prompt=prompt,
        input_payload=payload.options,
        status=CreationStatus.PENDING.value,
    )
    db.add(creation)
    await db.commit()
    await db.refresh(creation)
    return success(
        CreationRead.model_validate(creation).model_dump(),
        "创作任务已提交，等待 AI 服务处理",
    )


@router.get("", summary="我的 AI 作品")
async def list_creations(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict:
    filters = [AICreation.user_id == current_user.id]
    return success(
        await paginated(
            db,
            stmt=select(AICreation)
            .where(*filters)
            .order_by(AICreation.created_at.desc()),
            count_stmt=select(func.count(AICreation.id)).where(*filters),
            page=page,
            page_size=page_size,
            schema=CreationRead,
        )
    )


@router.get("/{creation_id}", summary="查询 AI 创作状态")
async def get_creation(
    creation_id: int, db: DbSession, current_user: CurrentUser
) -> dict:
    creation = await get_or_404(db, AICreation, creation_id, "AI 作品")
    if creation.user_id != current_user.id and current_user.role.code != "admin":
        raise HTTPException(status_code=403, detail="无权查看该作品")
    return success(CreationRead.model_validate(creation).model_dump())


@router.post("/{creation_id}/retry", summary="重试失败的 AI 创作")
async def retry_creation(
    creation_id: int, db: DbSession, current_user: CurrentUser
) -> dict:
    creation = await get_or_404(db, AICreation, creation_id, "AI 作品")
    if creation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权重试该作品")
    if creation.status not in {CreationStatus.FAILED.value, CreationStatus.PENDING.value}:
        raise HTTPException(status_code=409, detail="当前状态不允许重试")
    creation.status = CreationStatus.PENDING.value
    creation.error_message = None
    creation.retry_count += 1
    await db.commit()
    await db.refresh(creation)
    return success(CreationRead.model_validate(creation).model_dump(), "已重新进入处理队列")

