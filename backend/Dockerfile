# File:     backend/Dockerfile
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

# The SYNDICATE backend for hosting (Fly.io, Render or any Docker host).
# The database lives on a persistent disk mounted at /data. Run one instance only: SQLite and the
# results watcher both expect a single server.

FROM python:3.12.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SYNDICATE_ENV=production \
    SYNDICATE_DATABASE_URL=sqlite:////data/syndicate.db

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN useradd --create-home --uid 10001 syndicate && mkdir -p /data && chown syndicate /data
USER syndicate

EXPOSE 8080
# The host terminates HTTPS and forwards requests; trust its X-Forwarded-* headers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
