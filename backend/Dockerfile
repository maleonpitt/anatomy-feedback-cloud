# ---------- Base Image ----------
FROM python:3.10-slim

# ---------- Working Directory ----------
WORKDIR /app

# ---------- System Dependencies ----------
# (Required for Pandas, Excel reading, requests, and SSL)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        build-essential \
        python3-dev \
        libffi-dev \
        libssl-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------- Install Python Dependencies ----------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Copy Application Code ----------
COPY . .

# ---------- Create Non-Root User (Security Best Practice) ----------
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# ---------- Expose FastAPI/Uvicorn Port ----------
EXPOSE 5000

# ---------- Environment Variables ----------
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# ---------- Uvicorn Entrypoint ----------
#  - 3 workers for small API
#  - proxy-headers + forwarded-allow-ips for ALB X-Forwarded-* (TLS/scheme)
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--workers", "3", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
