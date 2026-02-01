#!/usr/bin/env bash
set -euo pipefail

exec uvicorn app:app \
  --app-dir jimeng-dify-service \
  --host 0.0.0.0 \
  --port "${PORT:-8080}"

