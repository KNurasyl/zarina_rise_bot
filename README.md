# Zarina Rise

A personal Telegram bot with a Mini App, built for one person. It helps keep a calm daily routine: meals, water, focus sessions, mood check-ins, a journal, sleep and small wins. There are no penalties for missed days; the bot suggests one small step at a time.

## What is in this repository

| Folder | What it is | Stack |
|---|---|---|
| `app` | Telegram bot and reminder scheduler | Python, aiogram, APScheduler, MongoDB |
| `api` | Backend for the Mini App | FastAPI, Pydantic, MongoDB |
| `mini-app` | Telegram Mini App | React, TypeScript, Vite |
| `deploy/nginx` | HTTPS reverse proxy | nginx, Let's Encrypt |
| `scripts` | Checks for content and scheduler logic, certificate scripts | Python, bash |

## How it works

- Reminders run on a schedule in the user's time zone. Before sending one, the scheduler checks quiet hours, pause mode, which reminder types are turned on and whether the action is already done today, so the bot does not repeat itself.
- Messages come from a library of templates for each reminder type: morning, meals, water, focus, sleep, mood support and others. A check script validates the templates before deploy.
- There is a reduced mode with fewer reminders for low-energy days.
- The Mini App opens inside Telegram. The API verifies Telegram `initData` with HMAC, and only Telegram accounts from an allow list can use the bot.

## Run locally

You need Docker. Copy `.env.example` to `.env`, fill in `BOT_TOKEN`, `MONGO_URI`, `MONGO_DB`, `ALLOWED_TELEGRAM_IDS`, `MINI_APP_URL` and `TIMEZONE`, then run:

```bash
docker compose up --build
```

Production setup is described in [README_DEPLOY.md](README_DEPLOY.md).
