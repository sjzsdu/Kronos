## Multi-stage build for smaller runtime image
## Stage 1: builder (collect wheels)
FROM python:3.12-slim AS builder
ARG INSTALL_TORCH=1
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /build
COPY csweb/requirements.txt requirements.txt
## Install build deps only if needed (torch wheels are prebuilt, but akshare may need build tools for lxml)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc g++ python3-dev curl \
 && pip install --upgrade pip \
 && if [ "$INSTALL_TORCH" = "1" ]; then \
        pip wheel --no-deps --wheel-dir /wheels -r requirements.txt; \
     else \
        grep -vi '^torch' requirements.txt > req.tmp && pip wheel --no-deps --wheel-dir /wheels -r req.tmp; \
     fi \
 && apt-get purge -y build-essential gcc g++ python3-dev \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

## Stage 2: runtime
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app \
    FLASK_APP=csweb/app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app
WORKDIR $APP_HOME
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*
## Copy all source code (build context is repo root)
COPY . .
## Verify model directory presence (fail-fast if missing)
RUN if [ ! -d ./model ]; then echo "[ERROR] ./model missing"; ls -al .; exit 1; fi
RUN useradd -m appuser && chown -R appuser:appuser $APP_HOME
USER appuser
EXPOSE 5001
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD curl -fsS http://localhost:5001/csweb/ || curl -fsS http://localhost:5001/ || exit 1
CMD ["python", "csweb/app.py"]
