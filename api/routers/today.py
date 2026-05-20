from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_telegram_id
from api.repositories import format_today_tasks, get_or_create_today_tasks, update_today_action
from api.schemas import TodayPatch

router = APIRouter()


@router.get("/today")
async def today(telegram_id: int = Depends(get_current_telegram_id)) -> dict:
    document = await get_or_create_today_tasks(telegram_id)
    return format_today_tasks(document)


@router.patch("/today")
async def update_today(
    payload: TodayPatch,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    if payload.key is not None:
        if payload.key == "water_count":
            if isinstance(payload.value, bool) or not isinstance(payload.value, int):
                raise HTTPException(status_code=400, detail="water_count value must be a number")
            if payload.value < 0 or payload.value > 20:
                raise HTTPException(status_code=400, detail="water_count value is out of range")
            return await update_today_action(
                telegram_id=telegram_id,
                key=payload.key,
                done=payload.value > 0,
                value=payload.value,
            )

        if not isinstance(payload.value, bool):
            raise HTTPException(status_code=400, detail=f"{payload.key} value must be boolean")

        return await update_today_action(
            telegram_id=telegram_id,
            key=payload.key,
            done=payload.value,
        )

    return await update_today_action(
        telegram_id=telegram_id,
        action=payload.action,
        key=payload.key,
        done=True if payload.done is None else payload.done,
        value=payload.value if isinstance(payload.value, int) and not isinstance(payload.value, bool) else None,
    )
