# Legacy production stack

> **LEGACY / REFERENCE ONLY**  
> **NOT PART OF TARGET ARCHITECTURE**  
> **DO NOT DEPLOY**

These files describe the **historical single-host deployment** where Nginx served the React build and proxied API traffic.

**Phase 7 retires Nginx from the target architecture.** The hypothetical production path is:

```text
Frontend: Browser → CloudFront → private S3 → React
Backend:  Browser → ALB → Target Group → EC2 → Uvicorn → FastAPI
```

## What moved where

| Former Nginx responsibility | New owner |
|-----------------------------|-----------|
| TLS for frontend | CloudFront + ACM |
| Static React files | Private S3 + CloudFront |
| SPA fallback (`try_files` / 404 → `index.html`) | CloudFront custom error responses |
| API reverse proxy | ALB → target group |
| Backend TLS termination | ALB |
| `/api` prefix strip | **Removed** — frontend calls API routes directly on the API host |

## Contents

| Path | Description |
|------|-------------|
| `nginx/default.conf` | Historical Nginx + Let's Encrypt + `/api` strip |
| `nginx/Dockerfile` | Nginx image build (legacy) |
| `docker-compose.production.yml` | Historical EC2 docker-compose layout |

## Local development

Do **not** use this folder for day-to-day development. See [`docs/LOCAL_DEVELOPMENT.md`](../docs/LOCAL_DEVELOPMENT.md).

`docker-compose.production.yml` is retained only as a reference for the live server layout.
