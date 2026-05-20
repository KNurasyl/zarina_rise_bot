from fastapi import APIRouter, Depends

from api.auth import get_current_telegram_id
from api.repositories import (
    cancel_focus_session,
    complete_focus_session,
    get_reactive_message,
    serialize_focus_session,
    serialize_template,
    start_focus_session,
)
from api.schemas import FocusComplete, FocusStart

router = APIRouter()


@router.post("/focus/start")
async def start_focus(
    payload: FocusStart,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    session = await start_focus_session(
        telegram_id=telegram_id,
        planned_minutes=payload.planned_minutes,
        label=payload.label,
    )
    return {"session": serialize_focus_session(session)}


@router.post("/focus/{session_id}/complete")
async def complete_focus(
    session_id: str,
    payload: FocusComplete,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    session = await complete_focus_session(
        telegram_id=telegram_id,
        session_id=session_id,
        completed_minutes=payload.completed_minutes,
        status=payload.status,
    )
    feedback = await get_reactive_message(
        telegram_id=telegram_id,
        action_type="after_focus",
        source_persona="bot",
        channel="mini_app",
    )
    return {
        "session": serialize_focus_session(session),
        "feedback": serialize_template(feedback),
    }


@router.post("/focus/{session_id}/cancel")
async def cancel_focus(
    session_id: str,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    session = await cancel_focus_session(telegram_id=telegram_id, session_id=session_id)
    return {"session": serialize_focus_session(session)}
