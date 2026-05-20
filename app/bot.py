import asyncio
import logging
from datetime import datetime
from random import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, CallbackQuery, InaccessibleMessage, Message

from app.access import deny_if_not_allowed, get_telegram_id, is_allowed_telegram_id
from app.config import BOT_TOKEN
from app.db import init_db
from app.keyboards import (
    FOCUS_TEXT,
    FOOD_TEXT,
    INSPIRATION_TEXT,
    JOURNAL_TEXT,
    MOOD_TEXT,
    NURASYL_TEXT,
    OPEN_APP_TEXT,
    PAUSE_TEXT,
    PROGRESS_TEXT,
    SETTINGS_TEXT,
    SLEEP_TEXT,
    TODAY_TEXT,
    WATER_TEXT,
    action_inline_keyboard,
    focus_inline_keyboard,
    main_keyboard,
    mini_app_inline_keyboard,
    mood_followup_inline_keyboard,
    mood_inline_keyboard,
    pause_inline_keyboard,
    today_inline_keyboard,
)
from app.repository import (
    activate_user,
    clear_pause,
    create_mood_checkin,
    deactivate_user,
    ensure_settings,
    get_compliment_by_settings,
    get_or_create_daily_tasks,
    get_progress_summary,
    get_random_compliment,
    get_reactive_message,
    mark_daily_action,
    pause_for_one_hour,
    pause_for_today,
    pause_until_evening,
    select_content_template,
    start_focus_session,
    upsert_user,
)
from app.scheduler import setup_scheduler
from app.seed import seed_contents

dp = Dispatcher()

HELP_TEXT = """
Zarina Rise — мягкая операционная система дня.

Я могу помочь с едой, водой, фокусом, настроением, дневником, маленькими победами, сном и тёплыми сообщениями от Нурасыла.

/today — краткий ритм дня
/focus — выбрать фокус на 15, 25 или 45 минут
/mood — коротко отметить настроение
/pause — поставить напоминания на мягкую паузу
/resume — вернуть напоминания
/compliment — получить бережный комплимент
/progress — посмотреть прогресс без давления
/settings — открыть настройки
/stop — отключить напоминания
""".strip()

START_TEXT = """
Добро пожаловать в Zarina Rise.

Это мягкая операционная система дня для Зарины: еда, вода, фокус, настроение, дневник, маленькие победы, сон и тёплые сообщения от Нурасыла.

Здесь нет давления и оценок за пропуски. Достаточно одного небольшого шага.
""".strip()

MOOD_LABELS = {
    "calm": "спокойно",
    "normal": "нормально",
    "tired": "устала",
    "anxious": "тревожно",
    "sad": "грустно",
    "overloaded": "перегруз",
    "no_energy": "нет сил",
    "productive": "продуктивно",
}

HEAVY_MOODS = {"overloaded", "no_energy", "anxious"}
RESOURCE_MOODS = {"calm", "productive"}

ACTION_LABELS = {
    "food": "еда",
    "water": "вода",
    "sleep": "сон",
    "focus": "фокус",
    "journal": "дневник",
    "mood": "настроение",
    "small_win": "маленькая победа",
    "pause": "пауза",
}


def build_mood_response(mood: str) -> str:
    mood_label = MOOD_LABELS.get(mood, "настроение")
    base = f"Отметила: {mood_label}. Без оценки: просто заметили состояние."

    if mood in HEAVY_MOODS:
        return (
            f"{base}\n\n"
            "Если сегодня тяжело, можно выбрать режим тише. "
            "Пусть сейчас будет один маленький шаг, не весь день сразу."
        )

    if mood in RESOURCE_MOODS:
        return (
            f"{base}\n\n"
            "Можно мягко направить этот ресурс в фокус или просто посмотреть план дня."
        )

    return f"{base}\n\nМожно продолжать спокойно, без длинных объяснений."


def format_pause_until(value: object) -> str:
    if not value:
        return "не включена"

    if isinstance(value, datetime):
        return value.strftime("%d.%m %H:%M UTC")

    return str(value)


def callback_telegram_id(callback: CallbackQuery) -> int:
    return callback.from_user.id


async def deny_callback_if_not_allowed(callback: CallbackQuery) -> bool:
    telegram_id = callback_telegram_id(callback)
    if is_allowed_telegram_id(telegram_id):
        return False

    await callback.answer("Недоступно для этого пользователя.", show_alert=True)
    return True


def next_daily_action(tasks: dict) -> str:
    if not (tasks.get("breakfast_done") and tasks.get("lunch_done") and tasks.get("dinner_done")):
        return "food"
    if int(tasks.get("water_count", 0)) < 2:
        return "water"
    if not tasks.get("focus_done"):
        return "focus"
    if not tasks.get("mood_done"):
        return "mood"
    if not tasks.get("journal_done"):
        return "journal"
    if not tasks.get("sleep_prep_done"):
        return "sleep"
    return "pause"


def format_today_summary(tasks: dict, intro: str) -> tuple[str, str]:
    completed = sum(
        [
            bool(tasks.get("breakfast_done")),
            bool(tasks.get("lunch_done")),
            bool(tasks.get("dinner_done")),
            int(tasks.get("water_count", 0)) > 0,
            bool(tasks.get("focus_done")),
            bool(tasks.get("mood_done")),
            bool(tasks.get("journal_done")),
            bool(tasks.get("small_win_done")),
            bool(tasks.get("sleep_prep_done")),
        ]
    )
    next_action = next_daily_action(tasks)
    lines = [
        intro,
        "",
        f"Сегодня: {completed}/9 мягких опор.",
        f"Еда: {sum(bool(tasks.get(key)) for key in ('breakfast_done', 'lunch_done', 'dinner_done'))}/3.",
        f"Вода: {int(tasks.get('water_count', 0))}.",
        f"Фокус: {'отмечен' if tasks.get('focus_done') else 'ещё можно выбрать короткий блок'}.",
        f"Настроение: {'отмечено' if tasks.get('mood_done') else 'можно сделать короткий чек-ин'}.",
        f"Дневник: {'есть запись' if tasks.get('journal_done') else 'можно оставить одну строку'}.",
        f"Сон: {'подготовка отмечена' if tasks.get('sleep_prep_done') else 'вечером можно закрыть день тише'}.",
    ]
    return "\n".join(lines), next_action


async def mini_app_answer(message: Message, text: str, path: str | None = None) -> None:
    await message.answer(text, reply_markup=mini_app_inline_keyboard(path))


async def safe_telegram_id(message: Message) -> int | None:
    telegram_id = get_telegram_id(message)
    if telegram_id is None:
        await message.answer("Не удалось определить пользователя.")
    return telegram_id


async def maybe_add_nurasyl_reactive(
    telegram_id: int,
    base_text: str,
    reactive_type: str,
) -> str:
    settings = await ensure_settings(telegram_id)
    if not settings.get("romantic_from_nurasyl_enabled", True):
        return base_text
    if random() >= 0.3:
        return base_text

    template = await get_reactive_message(
        telegram_id=telegram_id,
        action_type=reactive_type,
        source_persona="nurasyl",
        channel="bot",
    )
    if not template:
        return base_text

    return f"{base_text}\n\n{template['text']}"


async def mark_action_and_answer(message: Message, action: str) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    result = await mark_daily_action(telegram_id, action)
    reactive = await get_reactive_message(
        telegram_id=telegram_id,
        action_type=result["reactive_type"],
        source_persona="bot",
        channel="bot",
    )
    action_label = ACTION_LABELS.get(action, "действие")
    text = reactive["text"] if reactive else f"Отмечено: {action_label}."
    text = await maybe_add_nurasyl_reactive(telegram_id, text, result["reactive_type"])
    await message.answer(text, reply_markup=mini_app_inline_keyboard("today"))


async def send_template_text(
    message: Message,
    category: str,
    source_persona: str = "bot",
    path: str | None = None,
) -> None:
    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    template = await select_content_template(
        telegram_id=telegram_id,
        category=category,
        source_persona=source_persona,
        channel="bot",
        trigger="user_request",
    )
    text = template["text"] if template else "Можно выбрать один небольшой заботливый шаг."
    await message.answer(text, reply_markup=mini_app_inline_keyboard(path))


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await upsert_user(message)
    telegram_id = get_telegram_id(message)
    if telegram_id is not None:
        await ensure_settings(telegram_id)
        await activate_user(telegram_id)

    await message.answer(START_TEXT, reply_markup=main_keyboard)
    await mini_app_answer(message, "Mini App можно открыть здесь.", path="home")


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await message.answer(HELP_TEXT, reply_markup=main_keyboard)


@dp.message(Command("today"))
async def today_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    tasks = await get_or_create_daily_tasks(telegram_id)
    template = await select_content_template(
        telegram_id=telegram_id,
        category="morning",
        source_persona="bot",
        channel="bot",
        trigger="user_request",
    )
    intro = template["text"] if template else "Сегодня можно идти маленькими шагами."
    text, next_action = format_today_summary(tasks, intro)
    await message.answer(text, reply_markup=today_inline_keyboard(next_action))


@dp.message(Command("focus"))
async def focus_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    template = await select_content_template(
        telegram_id=telegram_id,
        category="focus_start",
        source_persona="bot",
        channel="bot",
        trigger="user_request",
    )
    text = template["text"] if template else "Выбери короткий фокус-блок. Можно начать мягко."
    await message.answer(text, reply_markup=focus_inline_keyboard())


@dp.message(Command("pause"))
async def pause_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    template = await select_content_template(
        telegram_id=telegram_id,
        category="pause",
        source_persona="bot",
        channel="bot",
        trigger="user_request",
    )
    text = template["text"] if template else "Можно поставить напоминания на мягкую паузу."
    await message.answer(text, reply_markup=pause_inline_keyboard())


@dp.message(Command("resume"))
async def resume_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    await activate_user(telegram_id)
    await clear_pause(telegram_id)
    await message.answer(
        "Пауза снята. Напоминания снова включены мягко и без давления.",
        reply_markup=main_keyboard,
    )


@dp.message(Command("compliment"))
async def compliment_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    template = await get_compliment_by_settings(telegram_id)
    text = template["text"] if template else "Ты делаешь маленькие шаги, и это уже важно."
    await message.answer(text, reply_markup=mini_app_inline_keyboard("home"))


@dp.message(Command("progress"))
async def progress_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    summary = await get_progress_summary(telegram_id)
    template = await select_content_template(
        telegram_id=telegram_id,
        category="progress_feedback",
        source_persona="bot",
        channel="bot",
        trigger="user_request",
    )
    intro = template["text"] if template else "Прогресс складывается из маленьких действий."
    await message.answer(
        (
            f"{intro}\n\n"
            f"Сегодня: {summary['completed_today']}/{summary['total_today']} опор.\n"
            f"Вода: {summary['water_count']}.\n"
            f"Настроение: {summary['mood_count']} чек-инов.\n"
            f"Записей в дневнике: {summary['journal_count']}.\n"
            f"Фокус-дней: {summary['focus_count']}."
        ),
        reply_markup=mini_app_inline_keyboard("progress"),
    )


@dp.message(Command("settings"))
async def settings_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    settings = await ensure_settings(telegram_id)
    reminders = "включены" if settings.get("reminders_enabled") else "выключены"
    romantic = "включены" if settings.get("romantic_from_nurasyl_enabled", True) else "выключены"
    pause_until = format_pause_until(settings.get("pause_until"))
    await message.answer(
        (
            f"Напоминания: {reminders}.\n"
            f"Сообщения от Нурасыла: {romantic}.\n"
            f"Пауза: {pause_until}.\n\n"
            "Остальные настройки можно аккуратно поменять в Mini App."
        ),
        reply_markup=mini_app_inline_keyboard("settings"),
    )


@dp.message(Command("stop"))
async def stop_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    await deactivate_user(telegram_id)
    await message.answer(
        "Напоминания отключены. Данные не удалены. Вернуть напоминания можно командой /resume.",
        reply_markup=main_keyboard,
    )


@dp.message(F.text == OPEN_APP_TEXT)
async def open_app_button_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await mini_app_answer(message, "Открыть Zarina Rise.", path="home")


@dp.message(F.text == TODAY_TEXT)
async def today_button_handler(message: Message) -> None:
    await today_handler(message)


@dp.message(F.text == FOCUS_TEXT)
async def focus_button_handler(message: Message) -> None:
    await focus_handler(message)


@dp.message(F.text == FOOD_TEXT)
async def food_button_handler(message: Message) -> None:
    await mark_action_and_answer(message, "food")


@dp.message(F.text == WATER_TEXT)
async def water_button_handler(message: Message) -> None:
    await mark_action_and_answer(message, "water")


@dp.message(F.text == SLEEP_TEXT)
async def sleep_button_handler(message: Message) -> None:
    await mark_action_and_answer(message, "sleep")


@dp.message(F.text == PAUSE_TEXT)
async def pause_button_handler(message: Message) -> None:
    await pause_handler(message)


@dp.message(F.text == NURASYL_TEXT)
async def nurasyl_button_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    telegram_id = await safe_telegram_id(message)
    if telegram_id is None:
        return

    template = await get_random_compliment(
        telegram_id=telegram_id,
        source_persona="nurasyl",
        channel="bot",
        trigger="user_request",
    )
    text = template["text"] if template else "От Нурасыла: я рядом тёплой мыслью."
    await message.answer(text, reply_markup=mini_app_inline_keyboard("home"))


@dp.message(F.text == INSPIRATION_TEXT)
async def inspiration_button_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await send_template_text(message, category="inspiration", source_persona="bot", path="home")


@dp.message(Command("mood"))
async def mood_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await message.answer("Как сейчас внутри? Можно выбрать без объяснений.", reply_markup=mood_inline_keyboard())


@dp.message(F.text == MOOD_TEXT)
async def mood_button_handler(message: Message) -> None:
    await mood_handler(message)


@dp.message(F.text == JOURNAL_TEXT)
async def journal_button_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await message.answer(
        "Дневник можно открыть в Mini App и оставить одну короткую строку.",
        reply_markup=action_inline_keyboard("journal", "journal"),
    )


@dp.message(F.text == PROGRESS_TEXT)
async def progress_button_handler(message: Message) -> None:
    await progress_handler(message)


@dp.message(F.text == SETTINGS_TEXT)
async def settings_button_handler(message: Message) -> None:
    await settings_handler(message)


@dp.callback_query(F.data.startswith("mark:"))
async def mark_callback_handler(callback: CallbackQuery) -> None:
    if await deny_callback_if_not_allowed(callback):
        return

    action = (callback.data or "").split(":", 1)[1]
    telegram_id = callback_telegram_id(callback)
    result = await mark_daily_action(telegram_id, action)
    reactive = await get_reactive_message(
        telegram_id=telegram_id,
        action_type=result["reactive_type"],
        source_persona="bot",
        channel="bot",
    )
    action_label = ACTION_LABELS.get(action, "действие")
    text = reactive["text"] if reactive else f"Отмечено: {action_label}."
    text = await maybe_add_nurasyl_reactive(telegram_id, text, result["reactive_type"])

    await callback.answer("Отмечено")
    if callback.message and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.answer(text, reply_markup=mini_app_inline_keyboard("today"))


@dp.callback_query(F.data.startswith("focus:start:"))
async def focus_start_callback_handler(callback: CallbackQuery) -> None:
    if await deny_callback_if_not_allowed(callback):
        return

    raw_minutes = (callback.data or "").rsplit(":", 1)[-1]
    try:
        minutes = int(raw_minutes)
        session = await start_focus_session(callback_telegram_id(callback), minutes)
    except ValueError:
        await callback.answer("Не удалось начать фокус", show_alert=True)
        return

    await callback.answer(f"Фокус {minutes} минут начат")
    if callback.message and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.answer(
            (
                f"Фокус на {session['planned_minutes']} минут начат.\n"
                "Когда закончишь, можно отметить фокус или продолжить в Mini App."
            ),
            reply_markup=action_inline_keyboard("focus", "focus"),
        )


@dp.callback_query(F.data.startswith("mood:"))
async def mood_callback_handler(callback: CallbackQuery) -> None:
    if await deny_callback_if_not_allowed(callback):
        return

    mood = (callback.data or "").split(":", 1)[1]
    telegram_id = callback_telegram_id(callback)
    try:
        await create_mood_checkin(telegram_id, mood)
    except ValueError:
        await callback.answer("Не удалось сохранить настроение", show_alert=True)
        return

    tasks = await get_or_create_daily_tasks(telegram_id)
    next_action = next_daily_action(tasks)
    text = build_mood_response(mood)

    await callback.answer("Сохранено")
    if callback.message and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.answer(
            text,
            reply_markup=mood_followup_inline_keyboard(mood, next_action),
        )


@dp.callback_query(F.data == "pause:1h")
async def pause_one_hour_callback_handler(callback: CallbackQuery) -> None:
    if await deny_callback_if_not_allowed(callback):
        return

    await pause_for_one_hour(callback_telegram_id(callback))
    await callback.answer("Пауза на 1 час")
    if callback.message and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.answer("Готово. Напоминания мягко отложены на 1 час.")


@dp.callback_query(F.data == "pause:evening")
async def pause_evening_callback_handler(callback: CallbackQuery) -> None:
    if await deny_callback_if_not_allowed(callback):
        return

    await pause_until_evening(callback_telegram_id(callback))
    await callback.answer("Пауза до вечера")
    if callback.message and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.answer("Готово. Напоминания на паузе до вечера.")


@dp.callback_query(F.data == "pause:today")
async def pause_today_callback_handler(callback: CallbackQuery) -> None:
    if await deny_callback_if_not_allowed(callback):
        return

    await pause_for_today(callback_telegram_id(callback))
    await callback.answer("Пауза на сегодня")
    if callback.message and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.answer("Готово. Сегодня будет тише. Вернуть напоминания можно через /resume.")


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить Zarina Rise"),
            BotCommand(command="help", description="Список возможностей"),
            BotCommand(command="today", description="Краткий ритм дня"),
            BotCommand(command="focus", description="Фокус 15/25/45 минут"),
            BotCommand(command="mood", description="Отметить настроение"),
            BotCommand(command="pause", description="Мягкая пауза"),
            BotCommand(command="resume", description="Вернуть напоминания"),
            BotCommand(command="compliment", description="Получить комплимент"),
            BotCommand(command="progress", description="Краткий прогресс"),
            BotCommand(command="settings", description="Открыть настройки"),
            BotCommand(command="stop", description="Отключить напоминания"),
        ]
    )


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing in .env")

    logging.basicConfig(level=logging.INFO)

    await init_db()
    await seed_contents()

    bot = Bot(token=BOT_TOKEN)
    scheduler = setup_scheduler(bot)

    try:
        await set_bot_commands(bot)
        scheduler.start()
        await dp.start_polling(bot)
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
