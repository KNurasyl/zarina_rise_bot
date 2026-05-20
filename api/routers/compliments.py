from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import ensure_settings, get_random_compliment, serialize_template
from api.schemas import ComplimentRandomRequest

router = APIRouter()


@router.post("/compliment/random")
async def random_compliment(
    payload: ComplimentRandomRequest,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    settings = await ensure_settings(telegram_id)
    source_persona = payload.source_persona or (
        "nurasyl"
        if settings.get("romantic_from_nurasyl_enabled", True)
        else "bot"
    )
    template = await get_random_compliment(
        telegram_id=telegram_id,
        source_persona=source_persona,
        channel="mini_app",
        trigger="user_request",
    )
    return {"template": serialize_template(template)}
