from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    ".pytest_cache",
}

BANNED_TERMS = (
    "\u0410\u043b\u0438\u0448\u0430\u043d",
    "\u043d\u0435 \u043f\u0438\u0441\u0430\u0442\u044c",
    "\u043d\u0435 \u043f\u0440\u043e\u0432\u0435\u0440\u044f\u0442\u044c",
    "\u043c\u0438\u043d\u0443\u0441\u044b",
    "40 \u0434\u043d\u0435\u0439 \u0431\u0435\u0437 \u043a\u043e\u043d\u0442\u0430\u043a\u0442\u0430",
    "\u043b\u043e\u043c\u043a\u0430",
    "\u043e\u0442\u043d\u043e\u0448\u0435\u043d\u0438\u044f",
)

SHAME_TERMS = (
    "\u0441\u0442\u044b\u0434",
    "\u043f\u043e\u0437\u043e\u0440",
    "\u043f\u0440\u043e\u0432\u0430\u043b",
    "\u043d\u0430\u043a\u0430\u0437",
    "\u043e\u0431\u044f\u0437\u0430\u043d\u0430",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def should_scan(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if SKIP_PARTS.intersection(relative.parts):
        return False
    if "migration" in str(relative).lower():
        return False
    return path.is_file()


def scan_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not should_scan(path):
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files.append(path)
    return files


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_function(source: str, signature: str) -> str:
    start = source.find(signature)
    assert_true(start >= 0, f"Function not found: {signature}")
    next_function = source.find("\n\nasync def ", start + 1)
    if next_function < 0:
        next_function = source.find("\n\ndef ", start + 1)
    if next_function < 0:
        return source[start:]
    return source[start:next_function]


def check_banned_terms() -> None:
    hits: list[str] = []
    for path in scan_text_files():
        text = read_text(path).lower()
        for term in BANNED_TERMS:
            if term.lower() in text:
                relative = path.relative_to(ROOT)
                hits.append(f"{relative}: {term}")

    assert_true(not hits, "Banned legacy terms found:\n" + "\n".join(hits))


def check_bot_privacy_contracts() -> None:
    source = read_text(ROOT / "app" / "repository.py")
    stop_body = extract_function(source, "async def deactivate_user")
    resume_body = extract_function(source, "async def activate_user")
    compliment_body = extract_function(source, "async def get_compliment_by_settings")

    assert_true('"reminders_enabled": False' in stop_body, "stop must disable reminders")
    assert_true('"is_active": False' not in stop_body, "stop must not delete/deactivate user")
    assert_true('"reminders_enabled": True' in resume_body, "resume must enable reminders")
    assert_true(
        "romantic_from_nurasyl_enabled" in compliment_body and "source_persona" in compliment_body,
        "compliment command must respect romantic settings",
    )


def check_notifications_do_not_store_journal_text() -> None:
    for relative in (Path("app/repository.py"), Path("api/repositories.py")):
        source = read_text(ROOT / relative)
        body = extract_function(source, "async def log_notification")
        assert_true('"text"' not in body and "'text'" not in body, f"{relative} logs text")


def check_auth_contracts() -> None:
    auth = read_text(ROOT / "api" / "auth.py")
    assert_true("X-Telegram-Init-Data" in auth, "API must read Telegram initData header")
    assert_true("hmac.compare_digest" in auth, "API must use constant-time hash compare")
    assert_true("ALLOWED_TELEGRAM_IDS" in auth, "API must enforce allowed Telegram ids")
    assert_true("ADMIN_TELEGRAM_IDS" in auth, "API must enforce admin ids")


def check_mini_app_contracts() -> None:
    app = read_text(ROOT / "mini-app" / "src" / "App.tsx")
    client = read_text(ROOT / "mini-app" / "src" / "api" / "client.ts")
    outside = read_text(ROOT / "mini-app" / "src" / "pages" / "OutsideTelegramPage.tsx")

    assert_true("!isTelegramMiniApp()" in app, "Mini App must block outside Telegram")
    assert_true("OutsideTelegramPage" in app and "Telegram" in outside, "Missing outside Telegram fallback")
    assert_true("ApiError" in client and "isAuthError" in client, "API client must expose auth errors")
    assert_true("status === 401" in client and "status === 403" in client, "API client must handle 401/403")
    assert_true("X-Telegram-Init-Data" in client, "API client must send Telegram initData")

    admin_hits: list[str] = []
    for path in (ROOT / "mini-app" / "src").rglob("*"):
        if not path.is_file():
            continue
        text = read_text(path)
        if "/admin" in text or "ADMIN_TELEGRAM_IDS" in text:
            admin_hits.append(str(path.relative_to(ROOT)))
    assert_true(not admin_hits, "Admin surface leaked into Mini App: " + ", ".join(admin_hits))


def check_progress_language() -> None:
    paths = (
        ROOT / "api" / "repositories.py",
        ROOT / "app" / "bot.py",
        ROOT / "mini-app" / "src" / "pages" / "ProgressPage.tsx",
    )
    hits: list[str] = []
    for path in paths:
        text = read_text(path).lower()
        for term in SHAME_TERMS:
            if term in text:
                hits.append(f"{path.relative_to(ROOT)}: {term}")
    assert_true(not hits, "Progress shame language found:\n" + "\n".join(hits))


def check_docker_contracts() -> None:
    local_compose = read_text(ROOT / "docker-compose.yml")
    prod_compose = read_text(ROOT / "docker-compose.prod.yml")
    mongo_block = prod_compose.split("  bot:", 1)[0]

    assert_true(
        "127.0.0.1:27017:27017" in local_compose,
        "Local Mongo port must be bound to localhost",
    )
    assert_true("ports:" not in mongo_block, "Prod Mongo must not publish ports")


def main() -> None:
    check_banned_terms()
    check_bot_privacy_contracts()
    check_notifications_do_not_store_journal_text()
    check_auth_contracts()
    check_mini_app_contracts()
    check_progress_language()
    check_docker_contracts()
    print("static QA contracts passed")


if __name__ == "__main__":
    main()
