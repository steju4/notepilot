# syntax=docker/dockerfile:1
# Optional local distribution, also used by deploy/compose.yaml.
FROM node:24-bookworm-slim AS frontend
ARG VITE_NOTEPILOT_HOSTED=0
ENV VITE_NOTEPILOT_HOSTED=$VITE_NOTEPILOT_HOSTED
WORKDIR /build
COPY frontend/package*.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci --strict-ssl=true
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ARG NOTEPILOT_INCLUDE_MODELS=0
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NOTEPILOT_DATA_DIR=/data
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN --mount=type=secret,id=system_ca \
    if [ -f /run/secrets/system_ca ]; then export PIP_CERT=/run/secrets/system_ca; fi; \
    python -m venv /app/.venv && /app/.venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
COPY scripts/homr-requirements.txt /tmp/homr-requirements.txt
RUN --mount=type=secret,id=system_ca \
    if [ -f /run/secrets/system_ca ]; then export PIP_CERT=/run/secrets/system_ca; fi; \
    python -m venv /app/.omr-venv && /app/.omr-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/homr-requirements.txt
COPY backend/app/ backend/app/
COPY scripts/ scripts/
COPY --from=frontend /build/dist/ frontend/dist/
RUN --mount=type=secret,id=system_ca \
    if [ -f /run/secrets/system_ca ]; then \
      export PIP_CERT=/run/secrets/system_ca REQUESTS_CA_BUNDLE=/run/secrets/system_ca SSL_CERT_FILE=/run/secrets/system_ca; \
    fi; \
    if [ "$NOTEPILOT_INCLUDE_MODELS" = "1" ]; then \
      NOTEPILOT_DATA_DIR=/opt/notepilot-seed /app/.venv/bin/python scripts/setup_omr.py; \
    fi
RUN groupadd --gid 10001 notepilot && useradd --uid 10001 --gid notepilot --create-home notepilot \
    && mkdir -p /data && chown notepilot:notepilot /data && chmod -R a+rX /app \
    && if [ -d /opt/notepilot-seed ]; then chmod -R a+rX /opt/notepilot-seed; fi
USER notepilot
EXPOSE 8000
CMD ["/app/.venv/bin/python", "scripts/container_start.py"]
