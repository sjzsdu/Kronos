# Use Python 3.9 slim image for optimal size/performance balance
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies, Python packages, and create directories in single optimized layer
RUN apt-get update && apt-get install -y \
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

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# Run the application
CMD ["python", "app.py"]
