from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import create_mood_checkin, serialize_document
from api.schemas import MoodCheckinCreate

router = APIRouter()


@router.post("/mood")
async def mood(
    payload: MoodCheckinCreate,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    document = await create_mood_checkin(
        telegram_id=telegram_id,
        mood=payload.mood,
        energy=payload.energy,
        note=payload.note,
    )
    return {"mood": serialize_document(document)}
