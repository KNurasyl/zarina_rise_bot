from pymongo import AsyncMongoClient

from api.config import MONGO_DB, MONGO_URI

client = AsyncMongoClient(MONGO_URI)
db = client[MONGO_DB]


async def init_db() -> None:
    await db.command("ping")

    await db.users.create_index("telegram_id", unique=True)
    await db.users.create_index("chat_id")
    await db.users.create_index("last_active_at")

    await db.settings.create_index("telegram_id", unique=True)

    await db.daily_tasks.create_index(
        [("telegram_id", 1), ("local_date", 1)],
        unique=True,
        partialFilterExpression={"local_date": {"$exists": True}},
    )

    await db.focus_sessions.create_index([("telegram_id", 1), ("started_at", 1)])
    await db.focus_sessions.create_index(
        "session_id",
        unique=True,
        partialFilterExpression={"session_id": {"$exists": True}},
    )

    await db.mood_checkins.create_index([("telegram_id", 1), ("created_at", 1)])

    await db.journal_entries.create_index([("telegram_id", 1), ("created_at", 1)])
    await db.journal_entries.create_index(
        "entry_id",
        unique=True,
        partialFilterExpression={"entry_id": {"$exists": True}},
    )

    await db.content_templates.create_index(
        [("category", 1), ("source_persona", 1), ("active", 1)]
    )
    await db.content_templates.create_index(
        "template_id",
        unique=True,
        partialFilterExpression={"template_id": {"$exists": True}},
    )

    await db.content_delivery_log.create_index([("telegram_id", 1), ("delivered_at", 1)])
    await db.content_delivery_log.create_index([("telegram_id", 1), ("template_id", 1)])

    await db.notifications_log.create_index([("telegram_id", 1), ("scheduled_for", 1)])

    await db.progress_events.create_index([("telegram_id", 1), ("created_at", 1)])
