#!/usr/bin/env bash
set -e

PORT=${PORT:-8000}

echo "listening on port $PORT..."

uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --proxy-headers \
    --forwarded-allow-ips="*"
