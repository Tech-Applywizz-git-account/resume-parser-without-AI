# ─────────────────────────────────────────────────────────────────────────────
# ApplyWizz Resume Parser — Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# curl is only needed for the Docker health-check probe.
# PyMuPDF ≥1.24 ships a self-contained manylinux wheel (MuPDF bundled),
# so no extra system libraries are required.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model
RUN python -m spacy download en_core_web_sm

# Copy application source
COPY . .

# Create uploads directory (ephemeral; files are deleted after parsing)
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run with multiple workers for production throughput.
# Use 2–4 workers per CPU core. Adjust WEB_CONCURRENCY via env var.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2}"]
