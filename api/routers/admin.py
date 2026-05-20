from fastapi import APIRouter, Depends, Query

from api.auth import get_current_admin_telegram_id
from api.repositories import (
    create_content_template_admin,
    disable_content_template_admin,
    list_content_templates_admin,
    seed_content_templates_admin,
    update_content_template_admin,
)
from api.schemas import ContentTemplateCreate, ContentTemplateUpdate, SeedContentRequest, SourcePersona

router = APIRouter(prefix="/admin")


@router.get("/content-templates")
async def list_content_templates(
    category: str | None = Query(default=None, min_length=1),
    source_persona: SourcePersona | None = Query(default=None),
    active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: int = Depends(get_current_admin_telegram_id),
) -> dict:
    return await list_content_templates_admin(
        category=category,
        source_persona=source_persona,
        active=active,
        limit=limit,
        offset=offset,
    )


@router.post("/content-templates")
async def create_content_template(
    payload: ContentTemplateCreate,
    _: int = Depends(get_current_admin_telegram_id),
) -> dict:
    return await create_content_template_admin(payload.model_dump())


@router.patch("/content-templates/{template_id}")
async def update_content_template(
    template_id: str,
    payload: ContentTemplateUpdate,
    _: int = Depends(get_current_admin_telegram_id),
) -> dict:
    return await update_content_template_admin(
        template_id=template_id,
        patch=payload.model_dump(exclude_unset=True),
    )


@router.post("/content-templates/{template_id}/disable")
async def disable_content_template(
    template_id: str,
    _: int = Depends(get_current_admin_telegram_id),
) -> dict:
    return await disable_content_template_admin(template_id)


@router.post("/content-templates/seed")
async def seed_content_templates(
    payload: SeedContentRequest = SeedContentRequest(),
    _: int = Depends(get_current_admin_telegram_id),
) -> dict:
    return await seed_content_templates_admin(overwrite_existing=payload.overwrite_existing)
