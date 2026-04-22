#!/bin/sh
set -eu

python - <<'PY'
import os
import socket
import time
from urllib.parse import urlparse

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise SystemExit(0)

normalized = database_url.replace("+asyncpg", "")
parsed = urlparse(normalized)
host = parsed.hostname or "db"
port = parsed.port or 5432
deadline = time.time() + 120

while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit(f"Database {host}:{port} did not become reachable in time")
PY

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
