FROM python:3.13-alpine AS base

WORKDIR /app

# Installed outside /app because compose mounts ./scripts over /app.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


FROM base AS test

COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN pip install --no-cache-dir -r /tmp/requirements-dev.txt

WORKDIR /work
