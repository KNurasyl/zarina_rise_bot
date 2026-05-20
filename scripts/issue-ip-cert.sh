#!/usr/bin/env bash
set -euo pipefail

SERVER_IP="${SERVER_IP:-0.0.0.0}"
LE_EMAIL="${LE_EMAIL:?LE_EMAIL is required}"

docker compose -f docker-compose.prod.yml -p zarina-rise stop nginx || true

docker run --rm \
  -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot:latest \
  certonly \
  --standalone \
  --non-interactive \
  --agree-tos \
  --email "$LE_EMAIL" \
  --preferred-profile shortlived \
  --ip-address "$SERVER_IP"

docker compose -f docker-compose.prod.yml -p zarina-rise up -d nginx
