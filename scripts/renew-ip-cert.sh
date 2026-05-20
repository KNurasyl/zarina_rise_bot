#!/usr/bin/env bash
set -euo pipefail

docker compose -f docker-compose.prod.yml -p zarina-rise stop nginx || true

docker run --rm \
  -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot:latest \
  renew \
  --non-interactive

docker compose -f docker-compose.prod.yml -p zarina-rise up -d nginx

docker exec zarina-rise-nginx nginx -s reload || true
