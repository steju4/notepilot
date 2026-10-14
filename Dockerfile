# Optional local distribution. No music is uploaded by this image.
FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NOTEPILOT_DATA_DIR=/data
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m venv /app/.venv && /app/.venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
COPY scripts/homr-requirements.txt /tmp/homr-requirements.txt
RUN python -m venv /app/.omr-venv && /app/.omr-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/homr-requirements.txt
COPY backend/app/ backend/app/
COPY scripts/ scripts/
COPY --from=frontend /build/dist/ frontend/dist/
RUN groupadd --gid 10001 notepilot && useradd --uid 10001 --gid notepilot --create-home notepilot && mkdir -p /data && chown notepilot:notepilot /data
USER notepilot
EXPOSE 8000
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "app.api:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
