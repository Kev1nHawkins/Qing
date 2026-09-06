from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, CurrentUser, DbSession
from app.api.helpers import apply_changes, get_or_404, paginated
from app.core.response import success
from app.models.creation import AICreation, CreationTemplate
from app.models.enums import CreationStatus, PublishStatus
from app.schemas.creation import (
    CreationRead,
    CreationRequest,
    FreeImageRequest,
    TemplateCreate,
    TemplateRead,
    TemplateUpdate,
)
from app.services.creation.prompt_service import CreationPromptService
from app.services.creation.template_validation import (
    validate_creation_options,
    validate_template_contract,
)
from app.services.creation.task_runner import (
    CreationTaskRunner,
    get_creation_task_runner,
)
from app.services.creation.system_templates import (
    SYSTEM_FREE_IMAGE_TEMPLATE_CODE,
    is_system_template,
)

router = APIRouter(prefix="/creations", tags=["Creation"])
FREE_IMAGE_SIZES = {
    "SQUARE": "1024x1024",
    "PORTRAIT": "768x1344",
    "LANDSCAPE": "1344x768",
}


@router.get("/templates", summary="AI 创作模板列表")
async def list_templates(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict:
    return success(
        await paginated(
            db,
            stmt=select(CreationTemplate)
            .where(
                CreationTemplate.status == PublishStatus.PUBLISHED.value,
                CreationTemplate.code != SYSTEM_FREE_IMAGE_TEMPLATE_CODE,
            )
            .order_by(CreationTemplate.id),
            count_stmt=select(func.count(CreationTemplate.id)).where(
                CreationTemplate.status == PublishStatus.PUBLISHED.value,
                CreationTemplate.code != SYSTEM_FREE_IMAGE_TEMPLATE_CODE,
            ),
            page=page,
            page_size=page_size,
            schema=TemplateRead,
        )
    )


@router.post("/templates", status_code=201, summary="新增 AI 创作模板")
async def create_template(
    payload: TemplateCreate, db: DbSession, _: AdminUser
) -> dict:
    if is_system_template(payload.code):
        raise HTTPException(status_code=409, detail="该编码由系统保留")
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
    if is_system_template(template.code):
        raise HTTPException(status_code=409, detail="系统模板不能通过管理接口修改")
    changes = payload.model_dump(exclude_unset=True)
    prompt_template = changes.get("prompt_template", template.prompt_template)
    options_schema = changes.get("options_schema", template.options_schema)
    if options_schema is None:
        raise HTTPException(status_code=422, detail="模板至少需要一个选项变量")
    try:
        validate_template_contract(prompt_template, options_schema)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    apply_changes(template, payload)
    await db.commit()
    await db.refresh(template)
    return success(TemplateRead.model_validate(template).model_dump(), "更新成功")


@router.post("", status_code=202, summary="提交异步 AI 创作")
async def create_creation(
    payload: CreationRequest,
    db: DbSession,
    current_user: CurrentUser,
    task_runner: Annotated[
        CreationTaskRunner,
        Depends(get_creation_task_runner),
    ],
) -> dict:
    template = await get_or_404(db, CreationTemplate, payload.template_id, "创作模板")
    if template.status != PublishStatus.PUBLISHED.value:
        raise HTTPException(status_code=409, detail="当前创作模板未发布")
    try:
        options = validate_creation_options(
            payload.options,
            template.options_schema or {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        prompt = CreationPromptService().build(
            template.prompt_template,
            options,
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"缺少模板选项：{exc.args[0]}") from exc
    creation = AICreation(
        user_id=current_user.id,
        template_id=template.id,
        culture_item_id=payload.culture_item_id or template.culture_item_id,
        title=payload.title,
        prompt=prompt,
        input_payload=options,
        status=CreationStatus.PENDING.value,
    )
    db.add(creation)
    await db.commit()
    await db.refresh(creation)
    task_runner.submit(creation.id)
    return success(
        CreationRead.model_validate(creation).model_dump(),
        "创作任务已提交，等待 AI 服务处理",
    )


@router.post("/free-image", status_code=202, summary="提交自由图片生成任务")
async def create_free_image(
    payload: FreeImageRequest,
    db: DbSession,
    current_user: CurrentUser,
    task_runner: Annotated[
        CreationTaskRunner,
        Depends(get_creation_task_runner),
    ],
) -> dict:
    template = await db.scalar(
        select(CreationTemplate).where(
            CreationTemplate.code == SYSTEM_FREE_IMAGE_TEMPLATE_CODE
        )
    )
    if not template:
        raise HTTPException(status_code=503, detail="自由图片功能尚未初始化")
    size = FREE_IMAGE_SIZES[payload.aspect_ratio]
    title_prompt = " ".join(payload.prompt.split())
    creation = AICreation(
        user_id=current_user.id,
        template_id=template.id,
        culture_item_id=None,
        title=f"自由创作 · {title_prompt[:36]}",
        prompt=payload.prompt,
        input_payload={
            "user_prompt": payload.prompt,
            "_kind": "FREE_IMAGE",
            "_aspect_ratio": payload.aspect_ratio,
            "_size": size,
        },
        status=CreationStatus.PENDING.value,
    )
    db.add(creation)
    await db.commit()
    await db.refresh(creation)
    task_runner.submit(creation.id)
    return success(
        CreationRead.model_validate(creation).model_dump(),
        "自由图片任务已提交，等待 AI 服务处理",
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
    creation_id: int,
    db: DbSession,
    current_user: CurrentUser,
    task_runner: Annotated[
        CreationTaskRunner,
        Depends(get_creation_task_runner),
    ],
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
    task_runner.submit(creation.id)
    return success(CreationRead.model_validate(creation).model_dump(), "已重新进入处理队列")

