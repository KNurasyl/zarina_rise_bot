import os

from dotenv import load_dotenv

load_dotenv(override=True)

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "growth_bot")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Almaty")
ALLOWED_TELEGRAM_IDS = [
    int(user_id.strip())
    for user_id in os.getenv("ALLOWED_TELEGRAM_IDS", "").split(",")
    if user_id.strip()
]
ADMIN_TELEGRAM_IDS = [
    int(user_id.strip())
    for user_id in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
    if user_id.strip()
]

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is missing")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")
