from urllib.parse import urlencode

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.config import MINI_APP_URL

OPEN_APP_TEXT = "🌸 Открыть Zarina Rise"
TODAY_TEXT = "📅 Сегодня"
FOCUS_TEXT = "🎯 Фокус"
FOOD_TEXT = "🍽 Еда"
WATER_TEXT = "💧 Вода"
SLEEP_TEXT = "🌙 Сон"
PAUSE_TEXT = "🫧 Пауза"
NURASYL_TEXT = "💌 От Нурасыла"
INSPIRATION_TEXT = "✨ Вдохновение"
MOOD_TEXT = "😊 Настроение"
JOURNAL_TEXT = "💭 Дневник"
PROGRESS_TEXT = "📈 Прогресс"
SETTINGS_TEXT = "⚙️ Настройки"


def mini_app_url(path: str | None = None) -> str | None:
    if not MINI_APP_URL:
        return None

    if not path:
        return MINI_APP_URL

    query = urlencode({"startapp": path.strip("/")})
    separator = "&" if "?" in MINI_APP_URL else "?"
    return f"{MINI_APP_URL}{separator}{query}"


def web_app_button(text: str, path: str | None = None) -> KeyboardButton:
    url = mini_app_url(path)
    if url:
        return KeyboardButton(text=text, web_app=WebAppInfo(url=url))
    return KeyboardButton(text=text)


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [web_app_button(OPEN_APP_TEXT, "home")],
        [KeyboardButton(text=TODAY_TEXT), KeyboardButton(text=FOCUS_TEXT)],
        [KeyboardButton(text=FOOD_TEXT), KeyboardButton(text=WATER_TEXT)],
        [KeyboardButton(text=SLEEP_TEXT), KeyboardButton(text=PAUSE_TEXT)],
        [KeyboardButton(text=NURASYL_TEXT), KeyboardButton(text=INSPIRATION_TEXT)],
        [KeyboardButton(text=MOOD_TEXT), KeyboardButton(text=JOURNAL_TEXT)],
        [KeyboardButton(text=PROGRESS_TEXT), KeyboardButton(text=SETTINGS_TEXT)],
    ],
    resize_keyboard=True,
)


def mini_app_inline_keyboard(path: str | None = None) -> InlineKeyboardMarkup | None:
    url = mini_app_url(path)
    if not url:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌸 Открыть Mini App",
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )


def action_inline_keyboard(action: str, path: str | None = None) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    url = mini_app_url(path or action)
    if url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🌸 Открыть Mini App",
                    web_app=WebAppInfo(url=url),
                )
            ]
        )

    buttons.extend(
        [
            [
                InlineKeyboardButton(text="✅ Отметить", callback_data=f"mark:{action}"),
                InlineKeyboardButton(text="Позже 1 час", callback_data="pause:1h"),
            ],
            [
                InlineKeyboardButton(text="🫧 Пауза сегодня", callback_data="pause:today"),
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def today_inline_keyboard(next_action: str) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Отметить следующий шаг",
                callback_data=f"mark:{next_action}",
            )
        ],
    ]
    url = mini_app_url("today")
    if url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🌸 Открыть Mini App",
                    web_app=WebAppInfo(url=url),
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(text="🫧 Сегодня тише", callback_data="pause:today"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def focus_inline_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="15 минут", callback_data="focus:start:15"),
            InlineKeyboardButton(text="25 минут", callback_data="focus:start:25"),
            InlineKeyboardButton(text="45 минут", callback_data="focus:start:45"),
        ]
    ]
    url = mini_app_url("focus")
    if url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🌸 Открыть focus flow",
                    web_app=WebAppInfo(url=url),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def pause_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 час", callback_data="pause:1h"),
                InlineKeyboardButton(text="До вечера", callback_data="pause:evening"),
            ],
            [
                InlineKeyboardButton(text="На сегодня", callback_data="pause:today"),
            ],
        ]
    )


def mood_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="😌 Спокойно", callback_data="mood:calm"),
                InlineKeyboardButton(text="🙂 Нормально", callback_data="mood:normal"),
            ],
            [
                InlineKeyboardButton(text="😐 Устала", callback_data="mood:tired"),
                InlineKeyboardButton(text="😰 Тревожно", callback_data="mood:anxious"),
            ],
            [
                InlineKeyboardButton(text="😞 Грустно", callback_data="mood:sad"),
                InlineKeyboardButton(text="🔥 Перегруз", callback_data="mood:overloaded"),
            ],
            [
                InlineKeyboardButton(text="🪫 Нет сил", callback_data="mood:no_energy"),
                InlineKeyboardButton(text="🎯 Продуктивно", callback_data="mood:productive"),
            ],
        ]
    )


def mood_followup_inline_keyboard(mood: str, next_action: str = "today") -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    markable_action = next_action if next_action in {"food", "water", "focus", "journal", "sleep", "small_win"} else "water"

    if mood in {"overloaded", "no_energy", "anxious"}:
        buttons.extend(
            [
                [InlineKeyboardButton(text="🫧 Пауза сегодня", callback_data="pause:today")],
                [InlineKeyboardButton(text="✅ Один маленький шаг", callback_data=f"mark:{markable_action}")],
            ]
        )
    elif mood in {"calm", "productive"}:
        buttons.append(
            [
                InlineKeyboardButton(text="🎯 Фокус 25 мин", callback_data="focus:start:25"),
            ]
        )
        today_url = mini_app_url("today")
        if today_url:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="📅 Сегодня",
                        web_app=WebAppInfo(url=today_url),
                    )
                ]
            )
        else:
            buttons.append([InlineKeyboardButton(text="✅ Следующий шаг", callback_data=f"mark:{markable_action}")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Один маленький шаг", callback_data=f"mark:{markable_action}")])

    mood_url = mini_app_url("mood")
    if mood_url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🌸 Открыть Mood flow",
                    web_app=WebAppInfo(url=mood_url),
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
