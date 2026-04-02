FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
COPY docker-entrypoint.sh ./
COPY .env.example ./.env.example

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN chmod +x /app/docker-entrypoint.sh
RUN mkdir -p /var/log/emr

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
