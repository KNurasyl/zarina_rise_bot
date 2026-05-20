import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.append(str(Path(__file__).resolve().parents[1]))

import app.repository as repository
import app.scheduler as scheduler
from app.repository import filter_templates_by_cooldown


BASE_SETTINGS = {
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
    "pause_until": None,
}

BASE_TASKS = {
    "timezone": "Asia/Almaty",
    "breakfast_done": False,
    "lunch_done": False,
    "dinner_done": False,
    "water_count": 0,
    "focus_done": False,
    "mood_done": False,
    "sleep_prep_done": False,
}


def local_at(hour: int, minute: int) -> datetime:
    return datetime(
        2026,
        5,
        19,
        hour,
        minute,
        tzinfo=ZoneInfo("Asia/Almaty"),
    ).astimezone(timezone.utc)


async def always_zero_count(**_: object) -> int:
    return 0


async def main() -> None:
    original_count_between = scheduler.count_notifications_between
    original_count_weekly = scheduler.count_weekly_notifications
    scheduler.count_notifications_between = always_zero_count
    scheduler.count_weekly_notifications = always_zero_count

    lunch_tasks = {**BASE_TASKS, "lunch_done": True}
    lunch_decision = await scheduler.should_send_notification(
        telegram_id=1,
        category="lunch",
        settings=BASE_SETTINGS,
        daily_tasks=lunch_tasks,
        scheduled_for=local_at(13, 30),
    )
    assert not lunch_decision.should_send
    assert lunch_decision.skip_reason == "already_done"

    paused_settings = {
        **BASE_SETTINGS,
        "pause_until": local_at(9, 30) + timedelta(hours=1),
    }
    pause_decision = await scheduler.should_send_notification(
        telegram_id=1,
        category="breakfast",
        settings=paused_settings,
        daily_tasks=BASE_TASKS,
        scheduled_for=local_at(9, 30),
    )
    assert not pause_decision.should_send
    assert pause_decision.skip_reason == "pause_until"

    async def maxed_daily_count(**kwargs: object) -> int:
        return 8 if kwargs.get("category") is None else 0

    scheduler.count_notifications_between = maxed_daily_count
    max_decision = await scheduler.should_send_notification(
        telegram_id=1,
        category="breakfast",
        settings=BASE_SETTINGS,
        daily_tasks=BASE_TASKS,
        scheduled_for=local_at(9, 30),
    )
    assert not max_decision.should_send
    assert max_decision.skip_reason == "max_messages_per_day"

    scheduler.count_notifications_between = always_zero_count
    mood_tasks = {**BASE_TASKS, "mood_done": True}
    mood_decision = await scheduler.should_send_notification(
        telegram_id=1,
        category="mood_checkin",
        settings=BASE_SETTINGS,
        daily_tasks=mood_tasks,
        scheduled_for=local_at(17, 30),
    )
    assert not mood_decision.should_send
    assert mood_decision.skip_reason == "already_done"

    sleep_tasks = {**BASE_TASKS, "sleep_prep_done": True}
    sleep_decision = await scheduler.should_send_notification(
        telegram_id=1,
        category="sleep",
        settings=BASE_SETTINGS,
        daily_tasks=sleep_tasks,
        scheduled_for=local_at(22, 30),
    )
    assert not sleep_decision.should_send
    assert sleep_decision.skip_reason == "already_done"

    reduced_user = {
        "telegram_id": 1,
        "last_active_at": local_at(10, 0) - timedelta(days=8),
    }
    reduced_lunch_decision = await scheduler.should_send_notification(
        telegram_id=1,
        category="lunch",
        settings=BASE_SETTINGS,
        daily_tasks=BASE_TASKS,
        scheduled_for=local_at(13, 30),
        user=reduced_user,
    )
    assert not reduced_lunch_decision.should_send
    assert reduced_lunch_decision.skip_reason == "reduced_mode"

    reduced_evening_decision = await scheduler.should_send_notification(
        telegram_id=1,
        category="evening",
        settings=BASE_SETTINGS,
        daily_tasks=BASE_TASKS,
        scheduled_for=local_at(20, 30),
        user=reduced_user,
    )
    assert reduced_evening_decision.should_send

    now = datetime.now(timezone.utc)
    romantic_templates = [
        {
            "template_id": "nurasyl_romantic_soft_001",
            "category": "nurasyl_romantic_soft",
            "subcategory": "soft",
            "source_persona": "nurasyl",
            "cooldown_days": 30,
        },
        {
            "template_id": "nurasyl_romantic_care_001",
            "category": "nurasyl_romantic_care",
            "subcategory": "care",
            "source_persona": "nurasyl",
            "cooldown_days": 30,
        },
    ]
    romantic_available = filter_templates_by_cooldown(
        templates=romantic_templates,
        latest_delivery_by_template={
            "nurasyl_romantic_soft_001": now - timedelta(days=1)
        },
        now=now,
    )
    assert [template["template_id"] for template in romantic_available] == [
        "nurasyl_romantic_care_001"
    ]

    original_get_recent_subcategories = repository.get_recent_subcategories

    async def recent_soft_subcategory(**_: object) -> set[str]:
        return {"soft"}

    repository.get_recent_subcategories = recent_soft_subcategory
    try:
        selected_categories = {
            await repository.select_category_avoiding_recent_subcategory(
                telegram_id=1,
                categories=["nurasyl_romantic_soft", "nurasyl_romantic_care"],
                source_persona="nurasyl",
            )
            for _ in range(10)
        }
    finally:
        repository.get_recent_subcategories = original_get_recent_subcategories

    assert selected_categories == {"nurasyl_romantic_care"}

    calls: list[str] = []
    original_random_compliment = scheduler.get_random_compliment

    async def fake_random_compliment(**kwargs: object) -> dict[str, object]:
        calls.append(str(kwargs["source_persona"]))
        return {
            "template_id": "fake",
            "category": "fake",
            "subcategory": "fake",
            "source_persona": kwargs["source_persona"],
            "text": "fake",
        }

    scheduler.get_random_compliment = fake_random_compliment
    try:
        romantic_template = await scheduler.select_notification_template(
            telegram_id=1,
            category="romantic_from_nurasyl",
        )
        bot_template = await scheduler.select_notification_template(
            telegram_id=1,
            category="random_compliment",
        )
    finally:
        scheduler.get_random_compliment = original_random_compliment

    assert romantic_template["source_persona"] == "nurasyl"
    assert bot_template["source_persona"] == "bot"
    assert calls == ["nurasyl", "bot"]

    scheduler_instance = scheduler.setup_scheduler(bot=object())
    job_ids = {job.id for job in scheduler_instance.get_jobs()}
    expected_categories = {
        "morning",
        "breakfast",
        "focus",
        "water_morning",
        "lunch",
        "water_afternoon",
        "mood_checkin",
        "dinner",
        "evening",
        "sleep",
        "random_compliment",
        "romantic_from_nurasyl",
    }
    assert len(job_ids) == 12
    assert all(
        any(job_id.startswith(f"notification:{category}:") for job_id in job_ids)
        for category in expected_categories
    )

    scheduler.count_notifications_between = original_count_between
    scheduler.count_weekly_notifications = original_count_weekly
    print("scheduler logic checks passed")


if __name__ == "__main__":
    asyncio.run(main())
