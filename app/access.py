from aiogram.types import Message

from app.config import ALLOWED_TELEGRAM_IDS


def get_telegram_id(message: Message) -> int | None:
    if message.from_user is None:
        return None

    return message.from_user.id


def is_allowed_user(message: Message) -> bool:
    telegram_id = get_telegram_id(message)

    if telegram_id is None:
        return False

    return is_allowed_telegram_id(telegram_id)


def is_allowed_telegram_id(telegram_id: int) -> bool:
    if not ALLOWED_TELEGRAM_IDS:
        return True

    return telegram_id in ALLOWED_TELEGRAM_IDS


async def deny_if_not_allowed(message: Message) -> bool:
    if is_allowed_user(message):
        return False

    await message.answer("Этот бот доступен только выбранным пользователям.")
    return True
