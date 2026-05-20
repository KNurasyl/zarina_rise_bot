from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import get_settings, patch_settings
from api.schemas import SettingsPatch

router = APIRouter()


@router.get("/settings")
async def settings(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    return await get_settings(telegram_id)


@router.patch("/settings")
async def update_settings(
    payload: SettingsPatch,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    return await patch_settings(
        telegram_id=telegram_id,
        patch=payload.model_dump(exclude_unset=True),
    )
