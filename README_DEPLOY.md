# Zarina Rise Deploy

Production runs through Docker Compose:

- `zarina-rise-bot`: Telegram bot with polling
- `zarina-rise-api`: FastAPI backend
- `zarina-rise-mini-app`: React Mini App static frontend
- `zarina-rise-nginx`: HTTPS reverse proxy
- `zarina-rise-mongo`: MongoDB, not exposed publicly

Public entrypoint: `https://0.0.0.0`

## GitLab Variables

Add these variables in GitLab CI/CD settings:

```env
BOT_TOKEN=your_botfather_token
MONGO_ROOT_USERNAME=root
MONGO_ROOT_PASSWORD=***REMOVED***
MONGO_DB=growth_bot
MONGO_URI=mongodb://root:***REMOVED***@mongo:27017/growth_bot?authSource=admin
TIMEZONE=Asia/Almaty
ALLOWED_TELEGRAM_IDS=***REMOVED***,ID_ЗАРИНЫ
MINI_APP_URL=https://0.0.0.0
SERVER_IP=0.0.0.0
LE_EMAIL=your@email.com
```

`MONGO_ROOT_PASSWORD` and the password inside `MONGO_URI` must match.
Use a Mongo password without `@`, `:`, `/`, `?`, `#`, `&` unless you URL-encode it.

Mark `BOT_TOKEN` and `MONGO_ROOT_PASSWORD` as masked/protected. Do not commit `.env`.

## First Deploy

Open HTTP/HTTPS ports on the server:

```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw status
```

Run the GitLab pipeline. The first deploy may start bot, API, Mini App and Mongo, while Nginx can fail until the IP certificate exists. That is expected.

Issue the first Let's Encrypt IP certificate on the server:

```bash
cd /opt/zarina-rise
SERVER_IP=0.0.0.0 LE_EMAIL=your@email.com bash scripts/issue-ip-cert.sh
```

Then rerun the deploy pipeline.

## Checks

```bash
docker ps
docker logs -f zarina-rise-bot
docker logs -f zarina-rise-api
docker logs -f zarina-rise-mini-app
docker logs -f zarina-rise-nginx
docker logs -f zarina-rise-mongo
```

MongoDB must not publish a public port:

```bash
docker port zarina-rise-mongo
```

Expected output: nothing.

Check API health:

```bash
curl -k https://0.0.0.0/api/health
```

Open the Mini App URL:

```text
https://0.0.0.0
```

In BotFather:

- Open Mini Apps / Main App
- Set URL: `https://0.0.0.0`
- Preview/welcome media can be added later

In Telegram, the bot keyboard button `🌸 Открыть Zarina Rise` should open the Mini App.

## Certificate Renew

Let's Encrypt IP certificates are short-lived, roughly 160 hours. Renew every 3 days.

Add this cron entry on the server:

```cron
0 4 */3 * * cd /opt/zarina-rise && SERVER_IP=0.0.0.0 LE_EMAIL=your@email.com bash scripts/renew-ip-cert.sh >> /var/log/zarina-rise-cert-renew.log 2>&1
```

If renew is not configured, HTTPS will stop working after about 6 days.

## Local Checks

Python syntax:

```bash
python -m py_compile app/config.py app/db.py app/seed.py app/repository.py app/main.py app/bot.py app/keyboards.py app/test_mongo.py app/scheduler.py app/access.py api/main.py api/config.py api/db.py api/auth.py api/repositories.py api/schemas.py
```

Mini App build:

```bash
cd mini-app
npm install
npm run build
```

Compose config:

```bash
docker compose -f docker-compose.prod.yml -p zarina-rise config
```

## CI/CD Shape

Pipeline stages:

- `build`: builds bot, API, Mini App and Nginx images
- `deploy`: writes `.env` from GitLab Variables and runs Docker Compose
- `data`: prunes unused Docker images

Runner tag: `ci-cd`.

There is no separate SSL stage. Certificates are issued and renewed by server scripts.
