import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import HTTPException, Request

from api.config import ADMIN_TELEGRAM_IDS, ALLOWED_TELEGRAM_IDS, BOT_TOKEN


def verify_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)

    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing Telegram initData hash")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )
    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid Telegram initData")

    user_json = parsed.get("user")

    if not user_json:
        raise HTTPException(status_code=401, detail="Telegram user is missing")

    try:
        user = json.loads(user_json)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=401, detail="Invalid Telegram user") from error

    return user


async def get_current_telegram_id(request: Request) -> int:
    init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data:
        raise HTTPException(status_code=401, detail="X-Telegram-Init-Data is missing")

    user = verify_init_data(init_data)
    telegram_id = user.get("id")

    if not isinstance(telegram_id, int):
        raise HTTPException(status_code=401, detail="Telegram user id is missing")

    if ALLOWED_TELEGRAM_IDS and telegram_id not in ALLOWED_TELEGRAM_IDS:
        raise HTTPException(status_code=403, detail="User is not allowed")

    return telegram_id


async def get_current_admin_telegram_id(request: Request) -> int:
    telegram_id = await get_current_telegram_id(request)

    if not ADMIN_TELEGRAM_IDS or telegram_id not in ADMIN_TELEGRAM_IDS:
        raise HTTPException(status_code=403, detail="Admin access is required")

    return telegram_id
