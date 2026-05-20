from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import delete_me, ensure_user

router = APIRouter()


@router.get("/me")
async def me(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    await ensure_user(telegram_id)
    return {
        "telegram_id": telegram_id,
        "allowed": True,
    }


@router.delete("/me")
async def delete_current_user(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    return await delete_me(telegram_id)
