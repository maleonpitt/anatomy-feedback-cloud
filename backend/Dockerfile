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
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ---------- Expose FastAPI/Uvicorn Port ----------
EXPOSE 5000

# ---------- Environment Variables ----------
# Secrets must be injected at runtime (K8s Secret / Secrets Manager) — never bake into the image.
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV SKIP_AUTH=false

# ---------- Healthcheck (Docker / local; K8s uses probe paths in k8s/deployment.yaml) ----------
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://127.0.0.1:5000/health || exit 1

# ---------- Uvicorn Entrypoint ----------
# Bind 0.0.0.0 so kubelet/ALB can reach the pod.
# proxy-headers for ALB / Ingress X-Forwarded-* (TLS/scheme)
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--workers", "3", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
