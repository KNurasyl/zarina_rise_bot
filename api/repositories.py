from datetime import UTC, datetime, timedelta
from random import choices
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from api.config import TIMEZONE
from api.db import db

DEFAULT_TIMEZONE = "Asia/Almaty"
TODAY_FOCUS = "Один маленький шаг: позаботиться о себе и сделать важное без давления."

DAILY_TASKS = [
    ("breakfast_done", "Позавтракать"),
    ("lunch_done", "Пообедать"),
    ("dinner_done", "Поужинать"),
    ("water_count", "Вода"),
    ("focus_done", "Один фокус-блок"),
    ("journal_done", "Запись в дневнике"),
    ("mood_done", "Настроение"),
    ("small_win_done", "Маленькая победа"),
    ("sleep_prep_done", "Подготовиться ко сну"),
]
DAILY_TASK_KEYS = {key for key, _ in DAILY_TASKS}

TODAY_ACTION_TO_FIELD = {
    "breakfast": "breakfast_done",
    "lunch": "lunch_done",
    "dinner": "dinner_done",
    "water": "water_count",
    "focus": "focus_done",
    "journal": "journal_done",
    "mood": "mood_done",
    "sleep": "sleep_prep_done",
    "small_win": "small_win_done",
}
TODAY_FIELD_TO_ACTION = {field: action for action, field in TODAY_ACTION_TO_FIELD.items()}
TODAY_ACTION_TITLES = {
    "breakfast": "Позавтракать",
    "lunch": "Пообедать",
    "dinner": "Поужинать",
    "water": "Вода",
    "focus": "Фокус",
    "journal": "Дневник",
    "mood": "Настроение",
    "sleep": "Подготовка ко сну",
    "small_win": "Маленькая победа",
}

TODAY_REACTIVE_ACTIONS = {
    "breakfast": "after_meal",
    "lunch": "after_meal",
    "dinner": "after_meal",
    "water": "after_meal",
    "focus": "after_focus",
    "journal": "after_journal",
    "mood": "after_journal",
    "sleep": "after_sleep_prep",
    "small_win": "after_journal",
}

JOURNAL_TYPES = {"note", "win", "gratitude", "idea", "focus", "evening"}
MOODS = {
    "calm",
    "normal",
    "tired",
    "anxious",
    "sad",
    "overloaded",
    "no_energy",
    "productive",
}
FOCUS_STATUSES = {"started", "completed", "partial", "cancelled"}
NOTIFICATION_STATUSES = {"sent", "skipped", "failed"}
COMPLIMENT_FREQUENCIES = {"low", "normal", "high"}
FOCUS_PLANNED_MINUTES = {15, 25, 45}
PAUSE_MODES = {"1h", "until_evening", "today"}

DEFAULT_SETTINGS = {
    "reminders_enabled": True,
    "morning_enabled": True,
    "meal_enabled": True,
    "water_enabled": True,
    "focus_enabled": True,
    "sleep_enabled": True,
    "mood_enabled": True,
    "random_compliments_enabled": True,
    "romantic_from_nurasyl_enabled": True,
    "compliment_frequency": "normal",
    "max_messages_per_day": 8,
    "quiet_hours_start": "22:30",
    "quiet_hours_end": "08:00",
    "preferred_wake_time": "08:30",
    "preferred_sleep_time": "23:30",
    "breakfast_time": "09:30",
    "lunch_time": "13:30",
    "dinner_time": "19:00",
    "focus_time": "10:00",
    "pause_until": None,
}

DAILY_TASK_DEFAULTS = {
    "breakfast_done": False,
    "lunch_done": False,
    "dinner_done": False,
    "water_count": 0,
    "focus_done": False,
    "journal_done": False,
    "mood_done": False,
    "small_win_done": False,
    "sleep_prep_done": False,
}

CONTENT_CATEGORY_ALIASES = {
    "today": "morning",
    "focus": "focus_start",
    "mood": "mood_normal",
    "no_energy": "mood_no_energy",
    "checkin": "mood_normal",
    "evening": "sleep",
    "compliment": "nurasyl_romantic_soft",
    "progress": "progress_feedback",
    "random_compliment": "nurasyl_romantic_soft",
}

BOT_COMPLIMENT_CATEGORIES = [
    "compliment_self_care",
    "compliment_discipline",
    "compliment_calm",
    "compliment_growth",
    "compliment_kindness",
    "compliment_work",
]

NURASYL_COMPLIMENT_CATEGORIES = [
    "nurasyl_romantic_soft",
    "nurasyl_romantic_morning",
    "nurasyl_romantic_work_support",
    "nurasyl_romantic_evening",
    "nurasyl_romantic_beauty_respectful",
    "nurasyl_romantic_proud_of_you",
    "nurasyl_romantic_missing_warmth",
    "nurasyl_romantic_care",
]

NURASYL_REACTIVE_CATEGORIES = {
    "meal": "nurasyl_after_meal",
    "after_meal": "nurasyl_after_meal",
    "focus": "nurasyl_after_focus",
    "after_focus": "nurasyl_after_focus",
    "journal": "nurasyl_after_journal",
    "after_journal": "nurasyl_after_journal",
    "mood": "nurasyl_after_mood",
    "after_mood": "nurasyl_after_mood",
    "sleep_prep": "nurasyl_after_sleep_prep",
    "after_sleep_prep": "nurasyl_after_sleep_prep",
    "bad_day": "nurasyl_after_bad_day",
    "after_bad_day": "nurasyl_after_bad_day",
}

BOT_REACTIVE_CATEGORIES = {
    "meal": "progress_feedback",
    "after_meal": "progress_feedback",
    "focus": "focus_complete",
    "after_focus": "focus_complete",
    "journal": "progress_feedback",
    "after_journal": "progress_feedback",
    "mood": "mood_normal",
    "after_mood": "mood_normal",
    "sleep_prep": "sleep",
    "after_sleep_prep": "sleep",
    "bad_day": "pause",
    "after_bad_day": "pause",
}

COMPLIMENT_SUBCATEGORIES = {
    "compliment_self_care": "self_care",
    "compliment_discipline": "discipline",
    "compliment_calm": "calm",
    "compliment_growth": "growth",
    "compliment_kindness": "kindness",
    "compliment_work": "work",
    "nurasyl_romantic_soft": "soft",
    "nurasyl_romantic_morning": "morning",
    "nurasyl_romantic_work_support": "work_support",
    "nurasyl_romantic_evening": "evening",
    "nurasyl_romantic_beauty_respectful": "beauty_respectful",
    "nurasyl_romantic_proud_of_you": "proud_of_you",
    "nurasyl_romantic_missing_warmth": "missing_warmth",
    "nurasyl_romantic_care": "care",
}

FALLBACK_TEXT = {
    "bot": "Мягкое напоминание: выбери один маленький заботливый шаг и продолжай без давления.",
    "nurasyl": "От Нурасыла: я рядом тёплой мыслью. Пусть следующий шаг будет к тебе бережным.",
}


def now_utc() -> datetime:
    return datetime.now(UTC)


def normalize_datetime(value: datetime | None) -> datetime:
    if value is None:
        return now_utc()

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    return normalize_datetime(value).isoformat()


def serialize_document(document: dict | None) -> dict | None:
    if document is None:
        return None

    serialized = {}
    for key, value in document.items():
        if key == "_id":
            continue
        if isinstance(value, datetime):
            serialized[key] = serialize_datetime(value)
        else:
            serialized[key] = value
    return serialized


def serialize_template(template: dict | None) -> dict | None:
    if template is None:
        return None

    allowed = {
        "template_id",
        "category",
        "subcategory",
        "source_persona",
        "tone",
        "text",
        "is_fallback",
    }
    return {key: value for key, value in template.items() if key in allowed}


def get_zoneinfo(timezone: str | None = None) -> ZoneInfo:
    return ZoneInfo(timezone or TIMEZONE or DEFAULT_TIMEZONE)


def local_date_string(timezone: str | None = None, moment: datetime | None = None) -> str:
    value = normalize_datetime(moment)
    return value.astimezone(get_zoneinfo(timezone)).date().isoformat()


def validate_time_string(value: str, field_name: str) -> None:
    try:
        hour_text, minute_text = value.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (AttributeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from error

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


def normalize_journal_type(entry_type: str) -> str:
    if entry_type not in JOURNAL_TYPES:
        raise HTTPException(status_code=400, detail="Invalid journal type")
    return entry_type


def serialize_journal_entry(entry: dict) -> dict:
    return {
        "id": entry.get("entry_id") or str(entry.get("_id")),
        "entry_id": entry.get("entry_id") or str(entry.get("_id")),
        "type": entry.get("type", "note"),
        "text": entry.get("text", ""),
        "tags": entry.get("tags", []),
        "created_at": serialize_datetime(entry.get("created_at")),
        "local_date": entry.get("local_date"),
        "is_deleted": bool(entry.get("is_deleted", False)),
    }


def weighted_choice(documents: list[dict]) -> dict | None:
    if not documents:
        return None

    weights = [max(1, int(document.get("weight") or 1)) for document in documents]
    return choices(documents, weights=weights, k=1)[0]


def normalize_content_category(category: str) -> str:
    return CONTENT_CATEGORY_ALIASES.get(category, category)


def infer_source_persona(category: str, source_persona: str | None = None) -> str:
    if source_persona:
        return source_persona

    if category.startswith("nurasyl_"):
        return "nurasyl"

    return "bot"


def is_compliment_or_romantic(category: str, source_persona: str | None) -> bool:
    return (
        source_persona == "nurasyl"
        or category.startswith("nurasyl_")
        or category.startswith("compliment_")
    )


def int_or_default(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def template_cooldown_days(template: dict) -> int:
    category = str(template.get("category") or "")
    source_persona = str(template.get("source_persona") or "")
    configured_days = max(0, int_or_default(template.get("cooldown_days"), 30))

    if is_compliment_or_romantic(category, source_persona):
        return max(30, configured_days)

    return configured_days


def subcategory_cooldown_days(category: str, source_persona: str | None) -> int:
    if not is_compliment_or_romantic(category, source_persona):
        return 0

    return 7


def fallback_template(
    category: str,
    source_persona: str,
    subcategory: str | None = None,
) -> dict:
    fallback_subcategory = subcategory or COMPLIMENT_SUBCATEGORIES.get(category) or "fallback"
    return {
        "template_id": f"fallback_{source_persona}_{category}_{fallback_subcategory}",
        "category": category,
        "subcategory": fallback_subcategory,
        "source_persona": source_persona,
        "tone": "romantic" if source_persona == "nurasyl" else "care",
        "text": FALLBACK_TEXT[source_persona],
        "active": True,
        "cooldown_days": 0,
        "weight": 1,
        "is_fallback": True,
    }


async def get_recent_subcategories(
    telegram_id: int,
    source_persona: str,
    delivered_after: datetime,
) -> set[str]:
    logs = await db.content_delivery_log.find(
        {
            "telegram_id": telegram_id,
            "source_persona": source_persona,
            "subcategory": {"$ne": None},
            "delivered_at": {"$gte": delivered_after},
        },
        {"subcategory": 1},
    ).to_list(length=None)
    return {log["subcategory"] for log in logs if log.get("subcategory")}


async def get_recent_template_delivery_map(
    telegram_id: int,
    templates: list[dict],
    delivered_after: datetime,
) -> dict[str, datetime]:
    template_ids = [template["template_id"] for template in templates]
    if not template_ids:
        return {}

    logs = await db.content_delivery_log.find(
        {
            "telegram_id": telegram_id,
            "template_id": {"$in": template_ids},
            "delivered_at": {"$gte": delivered_after},
        },
        {"template_id": 1, "delivered_at": 1},
    ).sort("delivered_at", -1).to_list(length=None)

    latest_by_template: dict[str, datetime] = {}
    for log in logs:
        template_id = log.get("template_id")
        if template_id and template_id not in latest_by_template:
            latest_by_template[template_id] = normalize_datetime(log.get("delivered_at"))

    return latest_by_template


def filter_templates_by_cooldown(
    templates: list[dict],
    latest_delivery_by_template: dict[str, datetime],
    now: datetime,
) -> list[dict]:
    available = []

    for template in templates:
        latest_delivery = latest_delivery_by_template.get(template["template_id"])
        cooldown_days = template_cooldown_days(template)

        if latest_delivery is None or latest_delivery < now - timedelta(days=cooldown_days):
            available.append(template)

    return available


async def ensure_settings(telegram_id: int) -> dict:
    now = now_utc()
    insert_document = {
        "telegram_id": telegram_id,
        **DEFAULT_SETTINGS,
        "updated_at": now,
    }

    try:
        await db.settings.update_one(
            {"telegram_id": telegram_id},
            {"$setOnInsert": insert_document},
            upsert=True,
        )
    except DuplicateKeyError:
        pass

    settings = await db.settings.find_one({"telegram_id": telegram_id})
    if settings is None:
        return insert_document

    missing_defaults = {
        key: value
        for key, value in DEFAULT_SETTINGS.items()
        if key not in settings
    }
    if missing_defaults:
        missing_defaults["updated_at"] = now
        await db.settings.update_one(
            {"telegram_id": telegram_id},
            {"$set": missing_defaults},
        )
        settings.update(missing_defaults)

    return settings


async def update_settings(telegram_id: int, patch: dict) -> dict:
    patch = dict(patch)
    allowed_keys = set(DEFAULT_SETTINGS)
    unknown_keys = set(patch) - allowed_keys

    if unknown_keys:
        raise HTTPException(status_code=400, detail="Unknown settings field")

    if "compliment_frequency" in patch and patch["compliment_frequency"] not in COMPLIMENT_FREQUENCIES:
        raise HTTPException(status_code=400, detail="Invalid compliment frequency")

    if "max_messages_per_day" in patch and patch["max_messages_per_day"] is not None:
        try:
            max_messages_per_day = int(patch["max_messages_per_day"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid max_messages_per_day") from None
        if not 1 <= max_messages_per_day <= 20:
            raise HTTPException(status_code=400, detail="Invalid max_messages_per_day")
        patch["max_messages_per_day"] = max_messages_per_day

    for field_name in (
        "quiet_hours_start",
        "quiet_hours_end",
        "preferred_wake_time",
        "preferred_sleep_time",
        "breakfast_time",
        "lunch_time",
        "dinner_time",
        "focus_time",
    ):
        if field_name in patch and patch[field_name] is not None:
            validate_time_string(patch[field_name], field_name)

    if "pause_until" in patch and patch["pause_until"] is not None:
        patch["pause_until"] = normalize_datetime(patch["pause_until"])

    await ensure_settings(telegram_id)
    patch["updated_at"] = now_utc()
    await db.settings.update_one({"telegram_id": telegram_id}, {"$set": patch})
    settings = await db.settings.find_one({"telegram_id": telegram_id})
    return settings or {}


async def set_reminders_enabled(telegram_id: int, enabled: bool) -> dict:
    return await update_settings(telegram_id, {"reminders_enabled": enabled})


async def ensure_user(
    telegram_id: int,
    chat_id: int | None = None,
    first_name: str | None = None,
    username: str | None = None,
) -> dict:
    now = now_utc()
    set_fields = {
        "updated_at": now,
        "last_active_at": now,
    }
    set_on_insert = {
        "telegram_id": telegram_id,
        "timezone": DEFAULT_TIMEZONE,
        "is_active": True,
        "onboarding_completed": False,
        "created_at": now,
    }

    optional_values = {
        "chat_id": chat_id,
        "first_name": first_name,
        "username": username,
    }
    for field_name, value in optional_values.items():
        if value is None:
            set_on_insert[field_name] = None
        else:
            set_fields[field_name] = value

    try:
        await db.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": set_fields, "$setOnInsert": set_on_insert},
            upsert=True,
        )
    except DuplicateKeyError:
        pass

    user = await db.users.find_one({"telegram_id": telegram_id})
    if user is None:
        user = {**set_on_insert, **set_fields}

    missing_defaults = {}
    for field_name, value in (
        ("timezone", DEFAULT_TIMEZONE),
        ("is_active", True),
        ("onboarding_completed", False),
        ("created_at", now),
    ):
        if field_name not in user or user.get(field_name) is None:
            missing_defaults[field_name] = value

    if missing_defaults:
        missing_defaults["updated_at"] = now
        await db.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": missing_defaults},
        )
        user.update(missing_defaults)

    await ensure_settings(telegram_id)
    return user


def get_active_day(user: dict) -> int:
    created_at = normalize_datetime(user.get("created_at"))
    timezone = user.get("timezone", DEFAULT_TIMEZONE)
    current_date = datetime.now(get_zoneinfo(timezone)).date()
    created_date = created_at.astimezone(get_zoneinfo(timezone)).date()
    return max(1, (current_date - created_date).days + 1)


def daily_task_defaults_from(document: dict | None = None) -> dict:
    source = document or {}
    defaults = dict(DAILY_TASK_DEFAULTS)
    defaults["breakfast_done"] = bool(
        source.get("breakfast_done", source.get("ate_well", defaults["breakfast_done"]))
    )
    defaults["water_count"] = int(source.get("water_count", defaults["water_count"]) or 0)
    defaults["focus_done"] = bool(
        source.get("focus_done", source.get("work_focus", defaults["focus_done"]))
    )
    defaults["small_win_done"] = bool(
        source.get("small_win_done", source.get("useful_action", defaults["small_win_done"]))
    )
    defaults["sleep_prep_done"] = bool(
        source.get("sleep_prep_done", source.get("sleep_on_time", defaults["sleep_prep_done"]))
    )
    return defaults


async def ensure_daily_task_shape(
    document: dict,
    local_date: str,
    timezone: str,
) -> dict:
    now = now_utc()
    defaults = {
        "date": local_date,
        "local_date": local_date,
        "timezone": timezone,
        **daily_task_defaults_from(document),
        "created_at": document.get("created_at", now),
    }
    set_fields = {
        key: value
        for key, value in defaults.items()
        if key not in document or document.get(key) is None
    }

    if set_fields:
        set_fields["updated_at"] = now
        await db.daily_tasks.update_one(
            {"_id": document["_id"]},
            {"$set": set_fields},
        )
        document.update(set_fields)

    return document


async def get_or_create_today_tasks(telegram_id: int) -> dict:
    user = await ensure_user(telegram_id)
    timezone = user.get("timezone", DEFAULT_TIMEZONE)
    local_date = local_date_string(timezone)
    document = await db.daily_tasks.find_one(
        {"telegram_id": telegram_id, "local_date": local_date}
    )

    if document:
        return await ensure_daily_task_shape(document, local_date, timezone)

    legacy_document = await db.daily_tasks.find_one(
        {"telegram_id": telegram_id, "date": local_date}
    )

    if legacy_document:
        return await ensure_daily_task_shape(legacy_document, local_date, timezone)

    now = now_utc()
    document = {
        "telegram_id": telegram_id,
        # Compatibility alias for the old unique telegram_id + date index.
        "date": local_date,
        "local_date": local_date,
        "timezone": timezone,
        **DAILY_TASK_DEFAULTS,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db.daily_tasks.update_one(
            {"telegram_id": telegram_id, "local_date": local_date},
            {"$setOnInsert": document},
            upsert=True,
        )
    except DuplicateKeyError:
        pass

    created = await db.daily_tasks.find_one(
        {"telegram_id": telegram_id, "local_date": local_date}
    )
    if created:
        return await ensure_daily_task_shape(created, local_date, timezone)

    legacy_document = await db.daily_tasks.find_one(
        {"telegram_id": telegram_id, "date": local_date}
    )
    if legacy_document:
        return await ensure_daily_task_shape(legacy_document, local_date, timezone)

    return document


def format_today_tasks(document: dict) -> dict:
    items = []
    completed_count = 0
    for key, title in DAILY_TASKS:
        value = document.get(key, 0 if key == "water_count" else False)
        done = value > 0 if key == "water_count" else bool(value)
        if done:
            completed_count += 1
        items.append(
            {
                "key": key,
                "action": TODAY_FIELD_TO_ACTION.get(key),
                "title": title,
                "done": done,
                "value": value,
            }
        )

    local_date = document.get("local_date") or document.get("date")
    return {
        "date": local_date,
        "local_date": local_date,
        "timezone": document.get("timezone", DEFAULT_TIMEZONE),
        "breakfast_done": bool(document.get("breakfast_done")),
        "lunch_done": bool(document.get("lunch_done")),
        "dinner_done": bool(document.get("dinner_done")),
        "water_count": int(document.get("water_count", 0)),
        "focus_done": bool(document.get("focus_done")),
        "journal_done": bool(document.get("journal_done")),
        "mood_done": bool(document.get("mood_done")),
        "small_win_done": bool(document.get("small_win_done")),
        "sleep_prep_done": bool(document.get("sleep_prep_done")),
        "completed_count": completed_count,
        "total_count": len(DAILY_TASKS),
        "items": items,
    }


async def update_today_task(telegram_id: int, key: str, done: bool) -> dict:
    if key not in DAILY_TASK_KEYS:
        raise HTTPException(status_code=400, detail="Unknown task key")

    document = await get_or_create_today_tasks(telegram_id)
    value = 1 if key == "water_count" and done else 0 if key == "water_count" else done
    await db.daily_tasks.update_one(
        {"_id": document["_id"]},
        {"$set": {key: value, "updated_at": now_utc()}},
    )
    document[key] = value
    document["updated_at"] = now_utc()

    if done:
        await create_progress_event(
            telegram_id=telegram_id,
            event_type=f"daily_task:{key}",
            value=1,
            source="today",
        )

    return document


def normalize_today_action(action: str | None = None, key: str | None = None) -> str:
    if action in TODAY_ACTION_TO_FIELD:
        return action

    if key in TODAY_FIELD_TO_ACTION:
        return TODAY_FIELD_TO_ACTION[key]

    if key in TODAY_ACTION_TO_FIELD:
        return key

    raise HTTPException(status_code=400, detail="Unknown today action")


async def update_today_action(
    telegram_id: int,
    action: str | None = None,
    key: str | None = None,
    done: bool = True,
    value: int | None = None,
) -> dict:
    normalized_action = normalize_today_action(action, key)
    field_name = TODAY_ACTION_TO_FIELD[normalized_action]
    document = await get_or_create_today_tasks(telegram_id)
    now = now_utc()

    if field_name == "water_count":
        next_value = value if value is not None else int(document.get("water_count", 0)) + (1 if done else 0)
        if not done and value is None:
            next_value = 0
        if next_value < 0 or next_value > 20:
            raise HTTPException(status_code=400, detail="water_count value is out of range")
        update = {"$set": {"water_count": next_value, "updated_at": now}}
        progress_value = next_value
    else:
        update = {"$set": {field_name: done, "updated_at": now}}
        progress_value = 1 if done else 0

    await db.daily_tasks.update_one({"_id": document["_id"]}, update)
    updated = await db.daily_tasks.find_one({"_id": document["_id"]})

    await create_progress_event(
        telegram_id=telegram_id,
        event_type=f"daily_task:{field_name}",
        value=progress_value,
        source="today",
        local_date=document.get("local_date"),
    )

    feedback = await get_reactive_message(
        telegram_id=telegram_id,
        action_type=TODAY_REACTIVE_ACTIONS[normalized_action],
        source_persona="bot",
        channel="mini_app",
    )
    return {
        "day": format_today_tasks(updated or document),
        "updated_action": normalized_action,
        "reactive_feedback": serialize_template(feedback),
    }


async def increment_water_count(telegram_id: int, amount: int = 1) -> dict:
    if amount < 1:
        raise HTTPException(status_code=400, detail="Water amount must be positive")

    document = await get_or_create_today_tasks(telegram_id)
    await db.daily_tasks.update_one(
        {"_id": document["_id"]},
        {
            "$inc": {"water_count": amount},
            "$set": {"updated_at": now_utc()},
        },
    )
    document["water_count"] = int(document.get("water_count", 0)) + amount
    document["updated_at"] = now_utc()
    await create_progress_event(
        telegram_id=telegram_id,
        event_type="water_logged",
        value=amount,
        source="today",
    )
    return document


async def create_mood_checkin(
    telegram_id: int,
    mood: str,
    energy: int | None = None,
    note: str | None = None,
) -> dict:
    if mood not in MOODS:
        raise HTTPException(status_code=400, detail="Invalid mood")

    user = await ensure_user(telegram_id)
    now = now_utc()
    document = {
        "telegram_id": telegram_id,
        "mood": mood,
        "energy": energy,
        "note": note,
        "created_at": now,
        "local_date": local_date_string(user.get("timezone"), now),
    }
    await db.mood_checkins.insert_one(document)
    today = await get_or_create_today_tasks(telegram_id)
    await db.daily_tasks.update_one(
        {"_id": today["_id"]},
        {"$set": {"mood_done": True, "updated_at": now}},
    )
    await create_progress_event(
        telegram_id=telegram_id,
        event_type="mood_checkin_created",
        value=1,
        source="mood",
    )
    return document


async def get_latest_mood_checkin(telegram_id: int) -> dict | None:
    document = await db.mood_checkins.find_one(
        {"telegram_id": telegram_id},
        sort=[("created_at", -1)],
    )
    return serialize_document(document)


async def create_journal_entry(
    telegram_id: int,
    entry_type: str,
    text: str,
    tags: list[str] | None = None,
) -> dict:
    if not text.strip():
        raise HTTPException(status_code=400, detail="Journal text is empty")

    user = await ensure_user(telegram_id)
    now = now_utc()
    normalized_type = normalize_journal_type(entry_type)
    cleaned_tags = []
    for tag in tags or []:
        value = tag.strip()
        if value:
            cleaned_tags.append(value[:40])
    document = {
        "telegram_id": telegram_id,
        "entry_id": str(uuid4()),
        "type": normalized_type,
        "text": text.strip(),
        "tags": cleaned_tags[:20],
        "created_at": now,
        "local_date": local_date_string(user.get("timezone"), now),
        "is_deleted": False,
    }
    await db.journal_entries.insert_one(document)

    update_fields = {"journal_done": True, "updated_at": now}
    if normalized_type == "win":
        update_fields["small_win_done"] = True
    today = await get_or_create_today_tasks(telegram_id)
    await db.daily_tasks.update_one(
        {"_id": today["_id"]},
        {"$set": update_fields},
    )

    await create_progress_event(
        telegram_id=telegram_id,
        event_type="journal_entry_created",
        value=1,
        source="journal",
        local_date=document["local_date"],
    )

    if normalized_type == "win":
        await create_progress_event(
            telegram_id=telegram_id,
            event_type="small_win_logged",
            value=1,
            source="journal",
            local_date=document["local_date"],
        )

    return serialize_journal_entry(document)


async def get_journal_entries(
    telegram_id: int,
    entry_type: str | None = None,
    local_date: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    query = {"telegram_id": telegram_id, "is_deleted": {"$ne": True}}
    if entry_type is not None:
        query["type"] = normalize_journal_type(entry_type)
    if local_date is not None:
        query["local_date"] = local_date

    cursor = (
        db.journal_entries.find(query)
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    entries = await cursor.to_list(length=limit)
    return [serialize_journal_entry(entry) for entry in entries]


async def start_focus_session(
    telegram_id: int,
    planned_minutes: int = 25,
    label: str | None = None,
) -> dict:
    if planned_minutes not in FOCUS_PLANNED_MINUTES:
        raise HTTPException(status_code=400, detail="planned_minutes must be 15, 25, or 45")

    user = await ensure_user(telegram_id)
    now = now_utc()
    document = {
        "telegram_id": telegram_id,
        "session_id": str(uuid4()),
        "planned_minutes": planned_minutes,
        "completed_minutes": 0,
        "label": label.strip() if label else None,
        "status": "started",
        "started_at": now,
        "completed_at": None,
        "local_date": local_date_string(user.get("timezone"), now),
    }
    await db.focus_sessions.insert_one(document)
    await get_or_create_today_tasks(telegram_id)
    await create_progress_event(
        telegram_id=telegram_id,
        event_type="focus_started",
        value=planned_minutes,
        source="focus",
        local_date=document["local_date"],
    )
    return document


def serialize_focus_session(session: dict | None) -> dict | None:
    return serialize_document(session)


async def complete_focus_session(
    telegram_id: int,
    session_id: str,
    completed_minutes: int,
    status: str = "completed",
) -> dict:
    if status not in {"completed", "partial"}:
        raise HTTPException(status_code=400, detail="Invalid focus status")

    if completed_minutes < 0 or completed_minutes > 180:
        raise HTTPException(status_code=400, detail="Invalid completed_minutes")

    completed_at = now_utc()
    update_result = await db.focus_sessions.update_one(
        {"telegram_id": telegram_id, "session_id": session_id},
        {
            "$set": {
                "completed_minutes": completed_minutes,
                "status": status,
                "completed_at": completed_at,
            }
        },
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Focus session not found")

    session = await db.focus_sessions.find_one(
        {"telegram_id": telegram_id, "session_id": session_id}
    )
    local_date = session.get("local_date") if session else local_date_string()
    if status in {"completed", "partial"} and completed_minutes >= 5:
        await db.daily_tasks.update_one(
            {"telegram_id": telegram_id, "local_date": local_date},
            {"$set": {"focus_done": True, "updated_at": completed_at}},
        )

    await create_progress_event(
        telegram_id=telegram_id,
        event_type=f"focus_{status}",
        value=completed_minutes,
        source="focus",
        local_date=local_date,
    )
    return session or {}


async def cancel_focus_session(telegram_id: int, session_id: str) -> dict:
    completed_at = now_utc()
    update_result = await db.focus_sessions.update_one(
        {"telegram_id": telegram_id, "session_id": session_id},
        {
            "$set": {
                "status": "cancelled",
                "completed_at": completed_at,
            }
        },
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Focus session not found")

    session = await db.focus_sessions.find_one(
        {"telegram_id": telegram_id, "session_id": session_id}
    )
    await create_progress_event(
        telegram_id=telegram_id,
        event_type="focus_cancelled",
        value=0,
        source="focus",
        local_date=(session or {}).get("local_date"),
    )
    return session or {}


async def create_content_template(
    category: str,
    text: str,
    subcategory: str | None = None,
    source_persona: str = "bot",
    tone: str | None = None,
    active: bool = True,
    cooldown_days: int = 30,
    weight: int = 1,
) -> dict:
    now = now_utc()
    document = {
        "template_id": str(uuid4()),
        "category": category,
        "subcategory": subcategory,
        "source_persona": source_persona,
        "tone": tone,
        "text": text.strip(),
        "active": active,
        "cooldown_days": cooldown_days,
        "weight": weight,
        "created_at": now,
        "updated_at": now,
    }
    await db.content_templates.insert_one(document)
    return document


async def get_content_template_for_delivery(
    telegram_id: int,
    category: str,
    subcategory: str | None = None,
    source_persona: str | None = None,
    channel: str = "bot",
    trigger: str = "scheduled",
) -> dict | None:
    return await select_content_template(
        telegram_id=telegram_id,
        category=category,
        source_persona=source_persona,
        subcategory=subcategory,
        channel=channel,
        trigger=trigger,
    )


async def select_content_template(
    telegram_id: int,
    category: str,
    source_persona: str | None = None,
    subcategory: str | None = None,
    channel: str = "bot",
    trigger: str = "scheduled",
) -> dict | None:
    normalized_category = normalize_content_category(category)
    effective_source = infer_source_persona(normalized_category, source_persona)
    query: dict = {"category": normalized_category, "active": True}
    if subcategory is not None:
        query["subcategory"] = subcategory
    if source_persona is not None or effective_source:
        query["source_persona"] = effective_source

    templates = await db.content_templates.find(query).to_list(length=None)
    now = now_utc()

    if templates:
        max_cooldown_days = max(template_cooldown_days(template) for template in templates)
        latest_delivery_by_template = await get_recent_template_delivery_map(
            telegram_id=telegram_id,
            templates=templates,
            delivered_after=now - timedelta(days=max_cooldown_days),
        )
        cooldown_available = filter_templates_by_cooldown(
            templates=templates,
            latest_delivery_by_template=latest_delivery_by_template,
            now=now,
        )
    else:
        cooldown_available = []

    selected = None
    if cooldown_available and is_compliment_or_romantic(normalized_category, effective_source):
        subcategory_days = subcategory_cooldown_days(normalized_category, effective_source)
        recent_subcategories = await get_recent_subcategories(
            telegram_id=telegram_id,
            source_persona=effective_source,
            delivered_after=now - timedelta(days=subcategory_days),
        )
        subcategory_available = [
            template
            for template in cooldown_available
            if template.get("subcategory") not in recent_subcategories
        ]
        selected = weighted_choice(subcategory_available or cooldown_available)
    elif cooldown_available:
        selected = weighted_choice(cooldown_available)

    if selected is None:
        selected = fallback_template(
            category=normalized_category,
            source_persona=effective_source,
            subcategory=subcategory,
        )

    await log_content_delivery(
        telegram_id=telegram_id,
        template=selected,
        channel=channel,
        trigger=trigger,
    )
    return selected


async def log_content_delivery(
    telegram_id: int,
    template: dict,
    channel: str,
    trigger: str,
) -> dict:
    user = await ensure_user(telegram_id)
    now = now_utc()
    document = {
        "telegram_id": telegram_id,
        "template_id": template["template_id"],
        "category": template.get("category"),
        "subcategory": template.get("subcategory"),
        "source_persona": template.get("source_persona", "bot"),
        "delivered_at": now,
        "local_date": local_date_string(user.get("timezone"), now),
        "channel": channel,
        "trigger": trigger,
    }
    await db.content_delivery_log.insert_one(document)
    return document


async def select_category_avoiding_recent_subcategory(
    telegram_id: int,
    categories: list[str],
    source_persona: str,
) -> str:
    recent_subcategories = await get_recent_subcategories(
        telegram_id=telegram_id,
        source_persona=source_persona,
        delivered_after=now_utc() - timedelta(days=7),
    )
    preferred_categories = [
        category
        for category in categories
        if COMPLIMENT_SUBCATEGORIES.get(category) not in recent_subcategories
    ]
    return choices(preferred_categories or categories, k=1)[0]


async def get_random_compliment(
    telegram_id: int,
    source_persona: str = "nurasyl",
    channel: str = "bot",
    trigger: str = "user_request",
) -> dict | None:
    categories = (
        NURASYL_COMPLIMENT_CATEGORIES
        if source_persona == "nurasyl"
        else BOT_COMPLIMENT_CATEGORIES
    )
    category = await select_category_avoiding_recent_subcategory(
        telegram_id=telegram_id,
        categories=categories,
        source_persona=source_persona,
    )
    return await select_content_template(
        telegram_id=telegram_id,
        category=category,
        source_persona=source_persona,
        channel=channel,
        trigger=trigger,
    )


async def get_scheduled_message(telegram_id: int, category: str) -> dict | None:
    normalized_category = normalize_content_category(category)
    if normalized_category in {"nurasyl_romantic_soft", "random_compliment"}:
        return await get_random_compliment(
            telegram_id=telegram_id,
            source_persona="nurasyl",
            channel="notification",
            trigger="scheduled",
        )

    source_persona = infer_source_persona(normalized_category)
    return await select_content_template(
        telegram_id=telegram_id,
        category=normalized_category,
        source_persona=source_persona,
        channel="notification",
        trigger="scheduled",
    )


async def get_reactive_message(
    telegram_id: int,
    action_type: str,
    source_persona: str = "bot",
    channel: str = "bot",
) -> dict | None:
    category_map = (
        NURASYL_REACTIVE_CATEGORIES
        if source_persona == "nurasyl"
        else BOT_REACTIVE_CATEGORIES
    )
    category = category_map.get(action_type)

    if category is None:
        category = "nurasyl_romantic_care" if source_persona == "nurasyl" else "progress_feedback"

    return await select_content_template(
        telegram_id=telegram_id,
        category=category,
        source_persona=source_persona,
        channel=channel,
        trigger="reactive",
    )


async def log_notification(
    telegram_id: int,
    category: str,
    scheduled_for: datetime,
    status: str,
    skip_reason: str | None = None,
    template_id: str | None = None,
    sent_at: datetime | None = None,
) -> dict:
    if status not in NOTIFICATION_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid notification status")

    document = {
        "telegram_id": telegram_id,
        "category": category,
        "scheduled_for": normalize_datetime(scheduled_for),
        "sent_at": normalize_datetime(sent_at) if sent_at else None,
        "status": status,
        "skip_reason": skip_reason,
        "template_id": template_id,
    }
    await db.notifications_log.insert_one(document)
    return document


async def create_progress_event(
    telegram_id: int,
    event_type: str,
    value: int | float | str | bool | None,
    source: str,
    local_date: str | None = None,
) -> dict:
    user = await ensure_user(telegram_id) if local_date is None else None
    now = now_utc()
    document = {
        "telegram_id": telegram_id,
        "event_type": event_type,
        "value": value,
        "created_at": now,
        "local_date": local_date or local_date_string(user.get("timezone") if user else None, now),
        "source": source,
    }
    await db.progress_events.insert_one(document)
    return document


def completed_task_count(day: dict) -> int:
    return sum(
        1
        for key, _ in DAILY_TASKS
        if (int(day.get(key, 0)) > 0 if key == "water_count" else bool(day.get(key)))
    )


def get_next_best_action(today: dict) -> dict | None:
    for action in ("breakfast", "water", "focus", "lunch", "mood", "journal", "small_win", "dinner", "sleep"):
        field_name = TODAY_ACTION_TO_FIELD[action]
        if field_name == "water_count":
            done = int(today.get(field_name, 0)) >= 2
        else:
            done = bool(today.get(field_name))
        if not done:
            return {
                "action": action,
                "title": TODAY_ACTION_TITLES[action],
                "message": "Один небольшой шаг будет достаточно.",
            }

    return {
        "action": "rest",
        "title": "Отдых",
        "message": "На сегодня уже есть хорошая опора. Можно идти мягче.",
    }


def rolling_dates(user: dict, days: int) -> list[str]:
    today = now_utc().astimezone(get_zoneinfo(user.get("timezone"))).date()
    return [(today - timedelta(days=offset)).isoformat() for offset in range(days)]


async def get_rolling_progress_summary(telegram_id: int, days: int) -> dict:
    user = await ensure_user(telegram_id)
    dates = rolling_dates(user, days)
    tasks = await db.daily_tasks.find(
        {"telegram_id": telegram_id, "local_date": {"$in": dates}}
    ).to_list(length=None)
    tasks_by_date = {
        task.get("local_date") or task.get("date"): task
        for task in tasks
        if task.get("local_date") or task.get("date")
    }

    completed_tasks = sum(completed_task_count(day) for day in tasks)
    days_with_support = sum(1 for day in tasks if completed_task_count(day) > 0)
    water_total = sum(int(day.get("water_count", 0)) for day in tasks)
    focus_days = sum(1 for day in tasks if day.get("focus_done"))
    sleep_prep_days = sum(1 for day in tasks if day.get("sleep_prep_done"))
    small_win_days = sum(1 for day in tasks if day.get("small_win_done"))

    focus_minutes_docs = await db.focus_sessions.find(
        {
            "telegram_id": telegram_id,
            "local_date": {"$in": dates},
            "status": {"$in": ["completed", "partial"]},
        },
        {"completed_minutes": 1},
    ).to_list(length=None)
    focus_minutes = sum(int(doc.get("completed_minutes", 0)) for doc in focus_minutes_docs)

    journal_count = await db.journal_entries.count_documents(
        {
            "telegram_id": telegram_id,
            "local_date": {"$in": dates},
            "is_deleted": {"$ne": True},
        }
    )
    mood_count = await db.mood_checkins.count_documents(
        {
            "telegram_id": telegram_id,
            "local_date": {"$in": dates},
        }
    )
    small_wins = await db.journal_entries.count_documents(
        {
            "telegram_id": telegram_id,
            "local_date": {"$in": dates},
            "type": "win",
            "is_deleted": {"$ne": True},
        }
    )

    return {
        "days": days,
        "days_with_support": days_with_support,
        "tasks_completed": completed_tasks,
        "tasks_possible": days * len(DAILY_TASKS),
        "completion_ratio": round(completed_tasks / (days * len(DAILY_TASKS)), 3),
        "support_actions_completed": completed_tasks,
        "water_count": water_total,
        "focus_days": focus_days,
        "focus_minutes": focus_minutes,
        "journal_count": journal_count,
        "mood_count": mood_count,
        "small_wins": max(small_wins, small_win_days),
        "sleep_prep_days": sleep_prep_days,
        "daily_supports": [
            {
                "local_date": local_date,
                "completed_count": completed_task_count(tasks_by_date.get(local_date, {})),
                "total_count": len(DAILY_TASKS),
            }
            for local_date in dates
        ],
        "note": "Прогресс показывает мягкий ритм и уже сделанные опоры.",
    }


async def get_dashboard(telegram_id: int) -> dict:
    user = await ensure_user(telegram_id)
    today = await get_or_create_today_tasks(telegram_id)
    local_date = today.get("local_date") or today.get("date")
    latest_entries = await get_journal_entries(telegram_id, limit=3)
    latest_mood = await get_latest_mood_checkin(telegram_id)
    progress_snapshot = await get_rolling_progress_summary(telegram_id, days=7)
    gentle_message = await select_content_template(
        telegram_id=telegram_id,
        category="inspiration",
        source_persona="bot",
        channel="mini_app",
        trigger="user_request",
    )

    message_of_day = serialize_template(gentle_message)
    return {
        "user": {
            "telegram_id": telegram_id,
            "timezone": user.get("timezone", DEFAULT_TIMEZONE),
            "active_day": get_active_day(user),
        },
        "local_date": local_date,
        "next_best_action": get_next_best_action(today),
        "today_summary": format_today_tasks(today),
        "latest_mood": latest_mood,
        "latest_journal_entries": latest_entries,
        "progress_snapshot": progress_snapshot,
        "message_of_day": message_of_day,
        "random_gentle_message": message_of_day,
    }


async def get_progress(telegram_id: int) -> dict:
    today = await get_or_create_today_tasks(telegram_id)
    rolling_7 = await get_rolling_progress_summary(telegram_id, days=7)
    rolling_30 = await get_rolling_progress_summary(telegram_id, days=30)
    rolling_40 = await get_rolling_progress_summary(telegram_id, days=40)

    return {
        "today": format_today_tasks(today),
        "rolling_7_day": rolling_7,
        "rolling_30_day": rolling_30,
        "rolling_40_day": rolling_40,
        "rolling_28_day": rolling_30,
        "soft_30_40_day_progress": {
            "last_30_days": rolling_30,
            "last_40_days": rolling_40,
            "note": "30/40 дней здесь показывают общий ритм, без требований к непрерывности.",
        },
        "focus_minutes": {
            "last_7_days": rolling_7["focus_minutes"],
            "last_30_days": rolling_30["focus_minutes"],
            "last_40_days": rolling_40["focus_minutes"],
            "last_28_days": rolling_30["focus_minutes"],
        },
        "journal_count": {
            "last_7_days": rolling_7["journal_count"],
            "last_30_days": rolling_30["journal_count"],
            "last_40_days": rolling_40["journal_count"],
            "last_28_days": rolling_30["journal_count"],
        },
        "mood_count": {
            "last_7_days": rolling_7["mood_count"],
            "last_30_days": rolling_30["mood_count"],
            "last_40_days": rolling_40["mood_count"],
            "last_28_days": rolling_30["mood_count"],
        },
        "small_wins": {
            "last_7_days": rolling_7["small_wins"],
            "last_30_days": rolling_30["small_wins"],
            "last_40_days": rolling_40["small_wins"],
            "last_28_days": rolling_30["small_wins"],
        },
        "support_completed": {
            "last_7_days": rolling_7["support_actions_completed"],
            "last_30_days": rolling_30["support_actions_completed"],
            "last_40_days": rolling_40["support_actions_completed"],
            "last_28_days": rolling_30["support_actions_completed"],
        },
        "daily_supports": {
            "today": format_today_tasks(today),
            "last_7_days": rolling_7["daily_supports"],
            "last_30_days": rolling_30["daily_supports"],
            "last_40_days": rolling_40["daily_supports"],
        },
        "message": "Здесь важна общая опора и мягкое возвращение к себе.",
    }


async def get_settings(telegram_id: int) -> dict:
    settings = await ensure_settings(telegram_id)
    return serialize_document(settings) or {}


async def patch_settings(telegram_id: int, patch: dict) -> dict:
    settings = await update_settings(telegram_id, patch)
    return serialize_document(settings) or {}


async def set_pause(
    telegram_id: int,
    mode: str = "1h",
    pause_until: datetime | None = None,
    minutes: int | None = 60,
    categories: list[str] | None = None,
) -> dict:
    if mode not in PAUSE_MODES:
        raise HTTPException(status_code=400, detail="Invalid pause mode")

    user = await ensure_user(telegram_id)
    now = now_utc()
    if pause_until is None:
        timezone_name = user.get("timezone", DEFAULT_TIMEZONE)
        now_local = now.astimezone(get_zoneinfo(timezone_name))
        if mode == "1h":
            pause_until = now + timedelta(minutes=minutes or 60)
        elif mode == "until_evening":
            evening = now_local.replace(hour=20, minute=30, second=0, microsecond=0)
            if evening <= now_local:
                evening = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
            pause_until = evening.astimezone(UTC)
        else:
            end_of_day = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
            pause_until = end_of_day.astimezone(UTC)

    normalized_until = normalize_datetime(pause_until)
    cleaned_categories = []
    for category in categories or []:
        value = category.strip()
        if value:
            cleaned_categories.append(value[:60])

    await ensure_settings(telegram_id)
    await db.settings.update_one(
        {"telegram_id": telegram_id},
        {
            "$set": {
                "pause_until": normalized_until,
                "pause_categories": cleaned_categories[:20],
                "updated_at": now,
            }
        },
    )
    await create_progress_event(
        telegram_id=telegram_id,
        event_type="pause_set",
        value=len(cleaned_categories),
        source="pause",
        local_date=local_date_string(user.get("timezone"), now),
    )
    settings = await db.settings.find_one({"telegram_id": telegram_id})
    return {
        "mode": mode,
        "pause_until": serialize_datetime(normalized_until),
        "categories": cleaned_categories[:20],
        "settings": serialize_document(settings),
    }


async def list_content_templates_admin(
    category: str | None = None,
    source_persona: str | None = None,
    active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    query: dict = {}
    if category:
        query["category"] = category
    if source_persona:
        query["source_persona"] = source_persona
    if active is not None:
        query["active"] = active

    cursor = (
        db.content_templates.find(query)
        .sort([("category", 1), ("template_id", 1)])
        .skip(offset)
        .limit(limit)
    )
    items = [serialize_document(document) for document in await cursor.to_list(length=limit)]
    total = await db.content_templates.count_documents(query)
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def create_content_template_admin(payload: dict) -> dict:
    now = now_utc()
    document = {
        **payload,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db.content_templates.insert_one(document)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail="Template already exists") from error

    return serialize_document(document) or {}


async def update_content_template_admin(template_id: str, patch: dict) -> dict:
    if not patch:
        template = await db.content_templates.find_one({"template_id": template_id})
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return serialize_document(template) or {}

    patch = dict(patch)
    patch["updated_at"] = now_utc()
    result = await db.content_templates.update_one(
        {"template_id": template_id},
        {"$set": patch},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")

    template = await db.content_templates.find_one({"template_id": template_id})
    return serialize_document(template) or {}


async def disable_content_template_admin(template_id: str) -> dict:
    return await update_content_template_admin(template_id, {"active": False})


async def seed_content_templates_admin(overwrite_existing: bool = False) -> dict:
    from app.content_seed import get_content_templates

    templates = get_content_templates()
    now = now_utc()
    inserted = 0
    updated = 0
    skipped = 0

    for template in templates:
        if overwrite_existing:
            result = await db.content_templates.update_one(
                {"template_id": template["template_id"]},
                {
                    "$set": {
                        **template,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    },
                },
                upsert=True,
            )
            if result.upserted_id:
                inserted += 1
            else:
                updated += result.modified_count
            continue

        result = await db.content_templates.update_one(
            {"template_id": template["template_id"]},
            {
                "$setOnInsert": {
                    **template,
                    "created_at": now,
                    "updated_at": now,
                }
            },
            upsert=True,
        )
        if result.upserted_id:
            inserted += 1
        else:
            skipped += 1

    return {
        "seeded": True,
        "overwrite_existing": overwrite_existing,
        "templates_total": len(templates),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
    }


async def get_export(telegram_id: int) -> dict:
    await ensure_user(telegram_id)
    collections = {
        "settings": db.settings,
        "daily_tasks": db.daily_tasks,
        "focus_sessions": db.focus_sessions,
        "mood_checkins": db.mood_checkins,
        "journal_entries": db.journal_entries,
    }
    export: dict = {
        "exported_at": serialize_datetime(now_utc()),
        "progress_summary": await get_progress(telegram_id),
    }

    for name, collection in collections.items():
        if name == "settings":
            export[name] = serialize_document(
                await collection.find_one({"telegram_id": telegram_id})
            )
        else:
            documents = await collection.find({"telegram_id": telegram_id}).to_list(length=None)
            export[name] = [serialize_document(document) for document in documents]

    return export


async def delete_me(telegram_id: int) -> dict:
    collections = [
        db.users,
        db.settings,
        db.daily_tasks,
        db.focus_sessions,
        db.mood_checkins,
        db.journal_entries,
        db.content_delivery_log,
        db.notifications_log,
        db.progress_events,
    ]
    deleted_counts = {}
    for collection in collections:
        result = await collection.delete_many({"telegram_id": telegram_id})
        deleted_counts[collection.name] = result.deleted_count

    return {
        "telegram_id": telegram_id,
        "deleted": True,
        "deleted_counts": deleted_counts,
    }
