from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import get_dashboard

router = APIRouter()


@router.get("/dashboard")
async def dashboard(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    return await get_dashboard(telegram_id)
