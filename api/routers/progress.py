from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import get_progress

router = APIRouter()


@router.get("/progress")
async def progress(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    return await get_progress(telegram_id)
