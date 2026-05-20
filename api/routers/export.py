from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import get_export

router = APIRouter()


@router.post("/export")
async def export_data(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    return await get_export(telegram_id)
