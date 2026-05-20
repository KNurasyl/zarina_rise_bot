from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import ALLOWED_TELEGRAM_IDS, TIMEZONE
from app.keyboards import mini_app_url
from app.repository import (
    count_notifications_between,
    count_weekly_notifications,
    ensure_settings,
    get_or_create_daily_tasks,
    get_random_compliment,
    log_content_delivery,
    log_notification,
    normalize_datetime,
    now_utc,
    select_content_template,
)

DEFAULT_TIMEZONE = "Asia/Almaty"
DEFAULT_WATER_TARGET = 2
DEFAULT_MAX_MESSAGES_PER_DAY = 8
REDUCED_MODE_AFTER_DAYS = 7
REDUCED_MODE_CATEGORIES = {"morning", "evening"}


@dataclass(frozen=True)
class NotificationDecision:
    should_send: bool
    skip_reason: str | None = None


CATEGORY_CONTENT_MAP = {
    "morning": "morning",
    "breakfast": "breakfast",
    "lunch": "lunch",
    "dinner": "dinner",
    "water_morning": "water",
    "water_afternoon": "water",
    "focus": "focus_start",
    "mood_checkin": "mood_normal",
    "evening": "progress_feedback",
    "sleep": "sleep",
}

CATEGORY_SETTING_MAP = {
    "morning": "morning_enabled",
    "breakfast": "meal_enabled",
    "lunch": "meal_enabled",
    "dinner": "meal_enabled",
    "water_morning": "water_enabled",
    "water_afternoon": "water_enabled",
    "focus": "focus_enabled",
    "mood_checkin": "mood_enabled",
    "evening": "sleep_enabled",
    "sleep": "sleep_enabled",
    "random_compliment": "random_compliments_enabled",
    "romantic_from_nurasyl": "romantic_from_nurasyl_enabled",
}

MEAL_DONE_FIELD = {
    "breakfast": "breakfast_done",
    "lunch": "lunch_done",
    "dinner": "dinner_done",
}

CATEGORY_ACTION_MAP = {
    "breakfast": "food",
    "lunch": "food",
    "dinner": "food",
    "water_morning": "water",
    "water_afternoon": "water",
    "focus": "focus",
    "mood_checkin": "mood",
    "sleep": "sleep",
}

CATEGORY_APP_PATH_MAP = {
    "morning": "home",
    "breakfast": "today",
    "lunch": "today",
    "dinner": "today",
    "water_morning": "today",
    "water_afternoon": "today",
    "focus": "focus",
    "mood_checkin": "today",
    "random_compliment": "home",
    "romantic_from_nurasyl": "home",
    "evening": "progress",
    "sleep": "today",
}

COMPLIMENT_NOTIFICATION_CATEGORIES = {"random_compliment", "romantic_from_nurasyl"}
COMPLIMENT_FREQUENCY_RULES = {
    "low": {"weekly_limit": 2, "weekdays": {1, 4}},
    "normal": {"weekly_limit": 4, "weekdays": {0, 2, 4, 6}},
    "high": {"weekly_limit": 7, "weekdays": {0, 1, 2, 3, 4, 5, 6}},
}


def parse_time(value: str | None, default: str) -> time:
    raw = value or default
    try:
        hour_text, minute_text = raw.split(":", 1)
        return time(hour=int(hour_text), minute=int(minute_text))
    except (TypeError, ValueError):
        hour_text, minute_text = default.split(":", 1)
        return time(hour=int(hour_text), minute=int(minute_text))


def int_setting(value: object, default: int) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default

    return parsed if parsed > 0 else default


def user_timezone(timezone_name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name or DEFAULT_TIMEZONE)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def is_quiet_hours(current_time: time, start: str | None, end: str | None) -> bool:
    quiet_start = parse_time(start, "22:30")
    quiet_end = parse_time(end, "08:00")

    if quiet_start <= quiet_end:
        return quiet_start < current_time < quiet_end

    return current_time > quiet_start or current_time < quiet_end


def is_pause_active(settings: dict, current_utc: datetime) -> bool:
    pause_until = settings.get("pause_until")
    if not pause_until:
        return False

    return normalize_datetime(pause_until) > current_utc


def is_category_enabled(category: str, settings: dict) -> bool:
    setting_key = CATEGORY_SETTING_MAP.get(category)
    if not setting_key:
        return True

    return bool(settings.get(setting_key, True))


def is_daily_action_done(category: str, daily_tasks: dict) -> bool:
    done_field = MEAL_DONE_FIELD.get(category)
    if done_field:
        return bool(daily_tasks.get(done_field))

    if category == "focus":
        return bool(daily_tasks.get("focus_done"))

    if category == "mood_checkin":
        return bool(daily_tasks.get("mood_done"))

    if category == "sleep":
        return bool(daily_tasks.get("sleep_prep_done"))

    return False


def is_water_enough(category: str, daily_tasks: dict) -> bool:
    if category not in {"water_morning", "water_afternoon"}:
        return False

    return int(daily_tasks.get("water_count", 0)) >= DEFAULT_WATER_TARGET


def week_start(current_local: datetime) -> datetime:
    start = current_local - timedelta(days=current_local.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)


def local_day_window_utc(current_local: datetime) -> tuple[datetime, datetime]:
    start_local = current_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def is_reduced_mode(user: dict | None, current_utc: datetime) -> bool:
    if not user:
        return False

    last_active_at = user.get("last_active_at")
    if not isinstance(last_active_at, datetime):
        return False

    return normalize_datetime(last_active_at) <= current_utc - timedelta(
        days=REDUCED_MODE_AFTER_DAYS
    )


async def is_compliment_frequency_allowed(
    telegram_id: int,
    category: str,
    settings: dict,
    current_local: datetime,
) -> NotificationDecision:
    if category not in COMPLIMENT_NOTIFICATION_CATEGORIES:
        return NotificationDecision(True)

    frequency = str(settings.get("compliment_frequency") or "normal")
    rule = COMPLIMENT_FREQUENCY_RULES.get(
        frequency,
        COMPLIMENT_FREQUENCY_RULES["normal"],
    )

    if current_local.weekday() not in rule["weekdays"]:
        return NotificationDecision(False, "frequency_day")

    sent_this_week = await count_weekly_notifications(
        telegram_id=telegram_id,
        category=category,
        since=week_start(current_local).astimezone(timezone.utc),
    )
    if sent_this_week >= rule["weekly_limit"]:
        return NotificationDecision(False, "frequency_limit")

    return NotificationDecision(True)


def notification_inline_keyboard(category: str) -> InlineKeyboardMarkup:
    action = CATEGORY_ACTION_MAP.get(category, "small_win")
    path = CATEGORY_APP_PATH_MAP.get(category, "home")
    buttons = [
        [
            InlineKeyboardButton(text="✅ Отметить", callback_data=f"mark:{action}"),
            InlineKeyboardButton(text="⏰ Позже", callback_data="pause:1h"),
        ],
        [
            InlineKeyboardButton(text="🫧 Пауза сегодня", callback_data="pause:today"),
        ],
    ]

    url = mini_app_url(path)
    if url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🌸 Открыть Mini App",
                    web_app=WebAppInfo(url=url),
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def should_send_notification(
    telegram_id: int,
    category: str,
    settings: dict,
    daily_tasks: dict,
    scheduled_for: datetime,
    user: dict | None = None,
) -> NotificationDecision:
    current_utc = normalize_datetime(scheduled_for)
    timezone_name = daily_tasks.get("timezone", DEFAULT_TIMEZONE)
    current_local = current_utc.astimezone(user_timezone(timezone_name))

    if not settings.get("reminders_enabled", True):
        return NotificationDecision(False, "reminders_disabled")

    if not is_category_enabled(category, settings):
        return NotificationDecision(False, "category_disabled")

    if is_quiet_hours(
        current_local.time(),
        settings.get("quiet_hours_start"),
        settings.get("quiet_hours_end"),
    ):
        return NotificationDecision(False, "quiet_hours")

    if is_pause_active(settings, current_utc):
        return NotificationDecision(False, "pause_until")

    reduced_mode = is_reduced_mode(user, current_utc)
    if reduced_mode and category not in REDUCED_MODE_CATEGORIES:
        return NotificationDecision(False, "reduced_mode")

    start_utc, end_utc = local_day_window_utc(current_local)
    max_messages_per_day = int_setting(
        settings.get("max_messages_per_day"),
        DEFAULT_MAX_MESSAGES_PER_DAY,
    )
    sent_today_total = await count_notifications_between(
        telegram_id=telegram_id,
        category=None,
        start_at=start_utc,
        end_at=end_utc,
        statuses=("sent",),
    )
    if sent_today_total >= max_messages_per_day:
        return NotificationDecision(False, "max_messages_per_day")

    sent_today_for_category = await count_notifications_between(
        telegram_id=telegram_id,
        category=category,
        start_at=start_utc,
        end_at=end_utc,
        statuses=("sent", "failed"),
    )
    if sent_today_for_category > 0:
        return NotificationDecision(False, "already_sent_today")

    if is_daily_action_done(category, daily_tasks):
        return NotificationDecision(False, "already_done")

    if is_water_enough(category, daily_tasks):
        return NotificationDecision(False, "water_enough")

    frequency_decision = await is_compliment_frequency_allowed(
        telegram_id=telegram_id,
        category=category,
        settings=settings,
        current_local=current_local,
    )
    if not frequency_decision.should_send:
        return frequency_decision

    return NotificationDecision(True)


async def select_notification_template(
    telegram_id: int,
    category: str,
    reduced_mode: bool = False,
) -> dict | None:
    if reduced_mode and category == "evening":
        return await select_content_template(
            telegram_id=telegram_id,
            category="reentry_after_silence",
            source_persona="bot",
            channel="notification",
            trigger="scheduled",
            log_delivery=False,
        )

    if category == "random_compliment":
        return await get_random_compliment(
            telegram_id=telegram_id,
            source_persona="bot",
            channel="notification",
            trigger="scheduled",
            log_delivery=False,
        )

    if category == "romantic_from_nurasyl":
        return await get_random_compliment(
            telegram_id=telegram_id,
            source_persona="nurasyl",
            channel="notification",
            trigger="scheduled",
            log_delivery=False,
        )

    content_category = CATEGORY_CONTENT_MAP.get(category)
    if not content_category:
        return None

    return await select_content_template(
        telegram_id=telegram_id,
        category=content_category,
        source_persona="bot",
        channel="notification",
        trigger="scheduled",
        log_delivery=False,
    )


async def send_notification_with_template(
    bot: Bot,
    user: dict,
    category: str,
    scheduled_for: datetime | None = None,
) -> None:
    scheduled_at = normalize_datetime(scheduled_for)
    telegram_id = user.get("telegram_id")
    chat_id = user.get("chat_id")

    if telegram_id is None:
        return

    if not user.get("is_active", True):
        await log_notification(
            telegram_id=telegram_id,
            category=category,
            scheduled_for=scheduled_at,
            status="skipped",
            skip_reason="user_inactive",
        )
        return

    if not chat_id:
        await log_notification(
            telegram_id=telegram_id,
            category=category,
            scheduled_for=scheduled_at,
            status="skipped",
            skip_reason="missing_chat_id",
        )
        return

    if ALLOWED_TELEGRAM_IDS and telegram_id not in ALLOWED_TELEGRAM_IDS:
        await log_notification(
            telegram_id=telegram_id,
            category=category,
            scheduled_for=scheduled_at,
            status="skipped",
            skip_reason="not_allowed",
        )
        return

    settings = await ensure_settings(telegram_id)
    daily_tasks = await get_or_create_daily_tasks(telegram_id)
    decision = await should_send_notification(
        telegram_id=telegram_id,
        category=category,
        settings=settings,
        daily_tasks=daily_tasks,
        scheduled_for=scheduled_at,
        user=user,
    )

    if not decision.should_send:
        await log_notification(
            telegram_id=telegram_id,
            category=category,
            scheduled_for=scheduled_at,
            status="skipped",
            skip_reason=decision.skip_reason,
        )
        return

    reduced_mode = is_reduced_mode(user, scheduled_at)
    template = await select_notification_template(
        telegram_id=telegram_id,
        category=category,
        reduced_mode=reduced_mode,
    )
    if not template:
        await log_notification(
            telegram_id=telegram_id,
            category=category,
            scheduled_for=scheduled_at,
            status="skipped",
            skip_reason="no_template",
        )
        return

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=template["text"],
            reply_markup=notification_inline_keyboard(category),
        )
    except Exception as error:
        await log_notification(
            telegram_id=telegram_id,
            category=category,
            scheduled_for=scheduled_at,
            status="failed",
            skip_reason=str(error),
            template_id=template.get("template_id"),
        )
        print(f"Notification send failed chat_id={chat_id}: {error}")
        return

    await log_content_delivery(
        telegram_id=telegram_id,
        template=template,
        channel="notification",
        trigger="scheduled",
    )
    await log_notification(
        telegram_id=telegram_id,
        category=category,
        scheduled_for=scheduled_at,
        sent_at=now_utc(),
        status="sent",
        template_id=template.get("template_id"),
    )


async def send_category_to_all_users(bot: Bot, category: str) -> None:
    from app.repository import get_active_users

    users = await get_active_users()
    scheduled_for = now_utc()

    for user in users:
        await send_notification_with_template(
            bot=bot,
            user=user,
            category=category,
            scheduled_for=scheduled_for,
        )


def add_category_job(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    category: str,
    hour: int,
    minute: int,
    day_of_week: str | None = None,
    jitter_seconds: int | None = None,
) -> None:
    scheduler.add_job(
        send_category_to_all_users,
        CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=TIMEZONE or DEFAULT_TIMEZONE,
            jitter=jitter_seconds,
        ),
        args=[bot, category],
        id=f"notification:{category}:{day_of_week or 'daily'}:{hour:02d}{minute:02d}",
        replace_existing=True,
    )


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE or DEFAULT_TIMEZONE)

    add_category_job(scheduler, bot, "morning", 8, 30)
    add_category_job(scheduler, bot, "breakfast", 9, 30)
    add_category_job(scheduler, bot, "focus", 10, 0, day_of_week="mon-fri")
    add_category_job(scheduler, bot, "water_morning", 11, 30)
    add_category_job(scheduler, bot, "lunch", 13, 30)
    add_category_job(scheduler, bot, "water_afternoon", 16, 30)
    add_category_job(scheduler, bot, "mood_checkin", 17, 30)
    add_category_job(scheduler, bot, "dinner", 19, 0)
    add_category_job(scheduler, bot, "evening", 20, 30)
    add_category_job(scheduler, bot, "sleep", 22, 30)

    # Jitter moves delivery inside the requested random windows.
    add_category_job(
        scheduler,
        bot,
        "random_compliment",
        11,
        0,
        jitter_seconds=9 * 60 * 60,
    )
    add_category_job(
        scheduler,
        bot,
        "romantic_from_nurasyl",
        10,
        0,
        jitter_seconds=12 * 60 * 60,
    )

    return scheduler
