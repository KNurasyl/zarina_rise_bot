from fastapi import APIRouter, Depends, Query

from api.auth import get_current_telegram_id
from api.repositories import create_journal_entry, get_journal_entries
from api.schemas import JournalEntryCreate, JournalEntryType

router = APIRouter()


@router.get("/journal")
async def journal_entries(
    entry_type: JournalEntryType | None = Query(default=None, alias="type"),
    local_date: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    entries = await get_journal_entries(
        telegram_id=telegram_id,
        entry_type=entry_type,
        local_date=local_date,
        limit=limit,
        offset=offset,
    )
    return {
        "items": entries,
        "limit": limit,
        "offset": offset,
    }


@router.post("/journal")
async def create_journal(
    payload: JournalEntryCreate,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    entry = await create_journal_entry(
        telegram_id=telegram_id,
        entry_type=payload.type,
        text=payload.text,
        tags=payload.tags,
    )
    return {"entry": entry}
