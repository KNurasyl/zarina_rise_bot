from datetime import datetime, timedelta, timezone
from random import choices
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from aiogram.types import Message
from pymongo.errors import DuplicateKeyError

from app.db import db

DEFAULT_TIMEZONE = "Asia/Almaty"
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
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime | None) -> datetime:
    if value is None:
        return now_utc()

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def local_date_string(
    timezone_name: str | None = None,
    moment: datetime | None = None,
) -> str:
    value = normalize_datetime(moment)
    return value.astimezone(ZoneInfo(timezone_name or DEFAULT_TIMEZONE)).date().isoformat()


def weighted_choice(documents: list[dict[str, Any]]) -> dict[str, Any] | None:
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


def int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def template_cooldown_days(template: dict[str, Any]) -> int:
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
) -> dict[str, Any]:
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


async def ensure_settings(telegram_id: int) -> dict[str, Any]:
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
    templates: list[dict[str, Any]],
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
    templates: list[dict[str, Any]],
    latest_delivery_by_template: dict[str, datetime],
    now: datetime,
) -> list[dict[str, Any]]:
    available = []

    for template in templates:
        latest_delivery = latest_delivery_by_template.get(template["template_id"])
        cooldown_days = template_cooldown_days(template)

        if latest_delivery is None or latest_delivery < now - timedelta(days=cooldown_days):
            available.append(template)

    return available


async def log_content_delivery(
    telegram_id: int,
    template: dict[str, Any],
    channel: str,
    trigger: str,
) -> dict[str, Any]:
    user = await db.users.find_one({"telegram_id": telegram_id})
    timezone_name = (user or {}).get("timezone", DEFAULT_TIMEZONE)
    now = now_utc()
    document = {
        "telegram_id": telegram_id,
        "template_id": template["template_id"],
        "category": template.get("category"),
        "subcategory": template.get("subcategory"),
        "source_persona": template.get("source_persona", "bot"),
        "delivered_at": now,
        "local_date": local_date_string(timezone_name, now),
        "channel": channel,
        "trigger": trigger,
    }
    await db.content_delivery_log.insert_one(document)
    return document


async def select_content_template(
    telegram_id: int,
    category: str,
    source_persona: str | None = None,
    subcategory: str | None = None,
    channel: str = "bot",
    trigger: str = "scheduled",
    log_delivery: bool = True,
) -> dict[str, Any] | None:
    normalized_category = normalize_content_category(category)
    effective_source = infer_source_persona(normalized_category, source_persona)
    query: dict[str, Any] = {"category": normalized_category, "active": True}
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

    if log_delivery:
        await log_content_delivery(
            telegram_id=telegram_id,
            template=selected,
            channel=channel,
            trigger=trigger,
        )
    return selected


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
    log_delivery: bool = True,
) -> dict[str, Any] | None:
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
        log_delivery=log_delivery,
    )


async def get_scheduled_message(telegram_id: int, category: str) -> dict[str, Any] | None:
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
) -> dict[str, Any] | None:
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


async def get_user_timezone(telegram_id: int) -> str:
    user = await db.users.find_one({"telegram_id": telegram_id}, {"timezone": 1})
    return (user or {}).get("timezone", DEFAULT_TIMEZONE)


def daily_task_defaults_from(document: dict[str, Any] | None = None) -> dict[str, Any]:
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

    for key, value in DAILY_TASK_DEFAULTS.items():
        if key not in defaults:
            defaults[key] = source.get(key, value)

    return defaults


async def ensure_daily_task_shape(
    document: dict[str, Any],
    local_date: str,
    timezone_name: str,
) -> dict[str, Any]:
    now = now_utc()
    defaults = {
        "date": local_date,
        "local_date": local_date,
        "timezone": timezone_name,
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


async def get_or_create_daily_tasks(telegram_id: int) -> dict[str, Any]:
    timezone_name = await get_user_timezone(telegram_id)
    local_date = local_date_string(timezone_name)
    document = await db.daily_tasks.find_one(
        {"telegram_id": telegram_id, "local_date": local_date}
    )

    if document:
        return await ensure_daily_task_shape(document, local_date, timezone_name)

    legacy_document = await db.daily_tasks.find_one(
        {"telegram_id": telegram_id, "date": local_date}
    )

    if legacy_document:
        return await ensure_daily_task_shape(legacy_document, local_date, timezone_name)

    now = now_utc()
    document = {
        "telegram_id": telegram_id,
        "date": local_date,
        "local_date": local_date,
        "timezone": timezone_name,
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
        return await ensure_daily_task_shape(created, local_date, timezone_name)

    legacy_document = await db.daily_tasks.find_one(
        {"telegram_id": telegram_id, "date": local_date}
    )
    if legacy_document:
        return await ensure_daily_task_shape(legacy_document, local_date, timezone_name)

    return document


async def mark_daily_action(telegram_id: int, action_type: str) -> dict[str, Any]:
    document = await get_or_create_daily_tasks(telegram_id)
    now = now_utc()
    update: dict[str, Any]

    if action_type == "food":
        timezone_name = document.get("timezone", DEFAULT_TIMEZONE)
        local_hour = now.astimezone(ZoneInfo(timezone_name)).hour
        if local_hour < 11:
            field = "breakfast_done"
        elif local_hour < 17:
            field = "lunch_done"
        else:
            field = "dinner_done"
        update = {"$set": {field: True, "updated_at": now}}
        progress_type = f"daily_task:{field}"
        reactive_type = "after_meal"
    elif action_type == "water":
        update = {
            "$inc": {"water_count": 1},
            "$set": {"updated_at": now},
        }
        progress_type = "water_logged"
        reactive_type = "after_meal"
    elif action_type == "sleep":
        update = {"$set": {"sleep_prep_done": True, "updated_at": now}}
        progress_type = "daily_task:sleep_prep_done"
        reactive_type = "after_sleep_prep"
    elif action_type == "focus":
        update = {"$set": {"focus_done": True, "updated_at": now}}
        progress_type = "daily_task:focus_done"
        reactive_type = "after_focus"
    elif action_type == "journal":
        update = {"$set": {"journal_done": True, "updated_at": now}}
        progress_type = "daily_task:journal_done"
        reactive_type = "after_journal"
    elif action_type == "mood":
        update = {"$set": {"mood_done": True, "updated_at": now}}
        progress_type = "daily_task:mood_done"
        reactive_type = "after_journal"
    elif action_type == "small_win":
        update = {"$set": {"small_win_done": True, "updated_at": now}}
        progress_type = "daily_task:small_win_done"
        reactive_type = "after_journal"
    elif action_type == "pause":
        update = {"$set": {"updated_at": now}}
        progress_type = "pause_marked"
        reactive_type = "after_bad_day"
    else:
        raise ValueError(f"Unknown daily action: {action_type}")

    await db.daily_tasks.update_one({"_id": document["_id"]}, update)
    await db.progress_events.insert_one(
        {
            "telegram_id": telegram_id,
            "event_type": progress_type,
            "value": 1,
            "created_at": now,
            "local_date": document.get("local_date"),
            "source": "bot",
        }
    )
    updated = await db.daily_tasks.find_one({"_id": document["_id"]})
    return {
        "daily_tasks": updated or document,
        "reactive_type": reactive_type,
    }


async def start_focus_session(
    telegram_id: int,
    planned_minutes: int,
    label: str | None = None,
) -> dict[str, Any]:
    if planned_minutes not in {15, 25, 45}:
        raise ValueError("planned_minutes must be one of 15, 25, 45")

    timezone_name = await get_user_timezone(telegram_id)
    now = now_utc()
    local_date = local_date_string(timezone_name, now)
    document = {
        "telegram_id": telegram_id,
        "session_id": str(uuid4()),
        "planned_minutes": planned_minutes,
        "completed_minutes": 0,
        "label": label,
        "status": "started",
        "started_at": now,
        "completed_at": None,
        "local_date": local_date,
    }
    await db.focus_sessions.insert_one(document)
    await get_or_create_daily_tasks(telegram_id)
    await db.progress_events.insert_one(
        {
            "telegram_id": telegram_id,
            "event_type": "focus_started",
            "value": planned_minutes,
            "created_at": now,
            "local_date": local_date,
            "source": "bot",
        }
    )
    return document


async def create_mood_checkin(
    telegram_id: int,
    mood: str,
    energy: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    if mood not in MOODS:
        raise ValueError(f"Unknown mood: {mood}")

    timezone_name = await get_user_timezone(telegram_id)
    now = now_utc()
    local_date = local_date_string(timezone_name, now)
    document = {
        "telegram_id": telegram_id,
        "mood": mood,
        "energy": energy,
        "note": note,
        "created_at": now,
        "local_date": local_date,
    }
    await db.mood_checkins.insert_one(document)

    daily_tasks = await get_or_create_daily_tasks(telegram_id)
    await db.daily_tasks.update_one(
        {"_id": daily_tasks["_id"]},
        {"$set": {"mood_done": True, "updated_at": now}},
    )
    await db.progress_events.insert_one(
        {
            "telegram_id": telegram_id,
            "event_type": "mood_checkin_created",
            "value": 1,
            "created_at": now,
            "local_date": local_date,
            "source": "bot",
        }
    )
    return document


async def set_pause_until(telegram_id: int, until: datetime) -> dict[str, Any]:
    normalized_until = normalize_datetime(until)
    await ensure_settings(telegram_id)
    await db.settings.update_one(
        {"telegram_id": telegram_id},
        {
            "$set": {
                "pause_until": normalized_until,
                "reminders_enabled": True,
                "updated_at": now_utc(),
            }
        },
    )
    settings = await db.settings.find_one({"telegram_id": telegram_id})
    return settings or {}


async def pause_for_one_hour(telegram_id: int) -> dict[str, Any]:
    return await set_pause_until(telegram_id, now_utc() + timedelta(hours=1))


async def pause_until_evening(telegram_id: int) -> dict[str, Any]:
    timezone_name = await get_user_timezone(telegram_id)
    now_local = now_utc().astimezone(ZoneInfo(timezone_name))
    evening = now_local.replace(hour=20, minute=30, second=0, microsecond=0)
    if evening <= now_local:
        evening = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
    return await set_pause_until(telegram_id, evening.astimezone(timezone.utc))


async def pause_for_today(telegram_id: int) -> dict[str, Any]:
    timezone_name = await get_user_timezone(telegram_id)
    now_local = now_utc().astimezone(ZoneInfo(timezone_name))
    end_of_day = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
    return await set_pause_until(telegram_id, end_of_day.astimezone(timezone.utc))


async def clear_pause(telegram_id: int) -> None:
    await ensure_settings(telegram_id)
    await db.settings.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"pause_until": None, "updated_at": now_utc()}},
    )


async def get_progress_summary(telegram_id: int) -> dict[str, Any]:
    today = await get_or_create_daily_tasks(telegram_id)
    journal_count = await db.journal_entries.count_documents(
        {"telegram_id": telegram_id, "is_deleted": {"$ne": True}}
    )
    mood_count = await db.mood_checkins.count_documents({"telegram_id": telegram_id})
    focus_count = await db.progress_events.count_documents(
        {"telegram_id": telegram_id, "event_type": "daily_task:focus_done"}
    )
    completed_today = sum(
        [
            bool(today.get("breakfast_done")),
            bool(today.get("lunch_done")),
            bool(today.get("dinner_done")),
            int(today.get("water_count", 0)) > 0,
            bool(today.get("focus_done")),
            bool(today.get("journal_done")),
            bool(today.get("mood_done")),
            bool(today.get("small_win_done")),
            bool(today.get("sleep_prep_done")),
        ]
    )
    return {
        "completed_today": completed_today,
        "total_today": 9,
        "water_count": int(today.get("water_count", 0)),
        "journal_count": journal_count,
        "mood_count": mood_count,
        "focus_count": focus_count,
    }


async def count_notifications_between(
    telegram_id: int,
    category: str | None,
    start_at: datetime,
    end_at: datetime,
    statuses: tuple[str, ...] = ("sent", "failed"),
) -> int:
    query: dict[str, Any] = {
        "telegram_id": telegram_id,
        "status": {"$in": list(statuses)},
        "scheduled_for": {
            "$gte": normalize_datetime(start_at),
            "$lt": normalize_datetime(end_at),
        },
    }

    if category is not None:
        query["category"] = category

    return await db.notifications_log.count_documents(query)


async def count_weekly_notifications(
    telegram_id: int,
    category: str,
    since: datetime,
) -> int:
    return await db.notifications_log.count_documents(
        {
            "telegram_id": telegram_id,
            "category": category,
            "status": "sent",
            "sent_at": {"$gte": normalize_datetime(since)},
        }
    )


async def log_notification(
    telegram_id: int,
    category: str,
    scheduled_for: datetime,
    status: str,
    skip_reason: str | None = None,
    template_id: str | None = None,
    sent_at: datetime | None = None,
) -> dict[str, Any]:
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


async def get_compliment_by_settings(telegram_id: int) -> dict[str, Any] | None:
    settings = await ensure_settings(telegram_id)
    source_persona = (
        "nurasyl"
        if settings.get("romantic_from_nurasyl_enabled", True)
        else "bot"
    )
    return await get_random_compliment(
        telegram_id=telegram_id,
        source_persona=source_persona,
        channel="bot",
        trigger="user_request",
    )


async def upsert_user(message: Message) -> None:
    user = message.from_user

    if user is None:
        return

    now = now_utc()
    await db.users.update_one(
        {"telegram_id": user.id},
        {
            "$set": {
                "telegram_id": user.id,
                "chat_id": message.chat.id,
                "first_name": user.first_name,
                "username": user.username,
                "is_active": True,
                "updated_at": now,
                "last_active_at": now,
            },
            "$setOnInsert": {
                "timezone": DEFAULT_TIMEZONE,
                "onboarding_completed": False,
                "created_at": now,
            },
        },
        upsert=True,
    )
    await db.users.update_one(
        {"telegram_id": user.id, "timezone": {"$exists": False}},
        {"$set": {"timezone": DEFAULT_TIMEZONE}},
    )
    await db.users.update_one(
        {"telegram_id": user.id, "onboarding_completed": {"$exists": False}},
        {"$set": {"onboarding_completed": False}},
    )
    await ensure_settings(user.id)


async def get_active_users() -> list[dict[str, Any]]:
    cursor = db.users.find({"is_active": True})
    return await cursor.to_list(length=None)


async def deactivate_user(telegram_id: int) -> None:
    now = now_utc()
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"updated_at": now, "last_active_at": now}},
    )
    await ensure_settings(telegram_id)
    await db.settings.update_one(
        {"telegram_id": telegram_id},
        {
            "$set": {
                "reminders_enabled": False,
                "updated_at": now,
            }
        },
        upsert=True,
    )


async def activate_user(telegram_id: int) -> None:
    now = now_utc()
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"is_active": True, "updated_at": now, "last_active_at": now}},
    )
    await ensure_settings(telegram_id)
    await db.settings.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"reminders_enabled": True, "pause_until": None, "updated_at": now}},
    )
