## Use Python 3.9 slim image for optimal size/performance balance
## IMPORTANT: Build context must be repository root (.) so that ./model is available
FROM python:3.9-slim

# Set working directory
WORKDIR /app

## Install system dependencies & Python packages in one layer (keeps image small)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ git curl build-essential python3-dev \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --upgrade pip \
 && pip install --no-cache-dir \
     flask==2.3.3 \
     flask-cors==4.0.0 \
     "pandas>=2.2.3,<3.0.0" \
     "numpy>=1.26.0,<2.0.0" \
     plotly==5.17.0 \
     "requests>=2.31.0" \
     "huggingface_hub>=0.20.0,<1.0.0" \
 && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
     "torch>=2.1.0,<2.3.0" || echo "Warning: torch installation failed, app will use fallback mode" \
 && pip install --no-cache-dir \
     "transformers>=4.35.0,<5.0.0" || echo "Warning: transformers installation failed, app will use fallback mode" \
 && pip install --no-cache-dir \
     "akshare>=1.14.0" || echo "Warning: akshare installation failed, app will use fallback mode" \
 && mkdir -p prediction_results cache templates \
 && apt-get remove -y gcc g++ build-essential \
 && apt-get autoremove -y \
 && apt-get clean


## Copy application code (assumes build context is repo root)
COPY csweb /app
COPY model /app/model

## Verify model directory presence (non-fatal)
RUN if [ ! -d /app/model ]; then echo "[WARN] /app/model missing. Kronos model import will fail."; else ls -al /app/model; fi

# Set environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5001

## Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

## Health check (use API health if implemented)
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -fsS http://localhost:5001/api/health || curl -fsS http://localhost:5001/ || exit 1

# Run the application
CMD ["python", "app.py"]
