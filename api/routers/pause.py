from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import set_pause
from api.schemas import PauseCreate

router = APIRouter()


@router.post("/pause")
async def pause(
    payload: PauseCreate,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    return await set_pause(
        telegram_id=telegram_id,
        mode=payload.mode,
        pause_until=payload.pause_until,
        minutes=payload.minutes,
        categories=payload.categories,
    )
