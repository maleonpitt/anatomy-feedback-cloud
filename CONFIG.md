# Configuration overview (Phase 8)

## Target architecture (hypothetical — local model only)

```text
Frontend: https://app.example.com  → CloudFront → private S3 (React build)
API:      https://api.example.com  → ALB → Uvicorn/FastAPI
```

Nginx is **retired** from the target model. Legacy files live under `legacy/`.

## Frontend build (public)

| Variable | Purpose |
|----------|---------|
| `REACT_APP_API_BASE_URL` | API origin, e.g. `http://localhost:5001` or `https://api.example.com` |

API calls use **direct FastAPI paths** (`/send-feedback`, not `/api/send-feedback`).  
The old Nginx `/api` strip is no longer part of the target architecture.

## Backend runtime (private)

| Variable | Purpose |
|----------|---------|
| `FRONTEND_URL` | Primary CORS origin + OAuth redirect |
| `CORS_ALLOWED_ORIGINS` | Optional comma-separated extras |
| `SESSION_COOKIE_*` | Cross-origin cookie flags |
| `CATEGORY_STORE_TYPE`, `CATEGORY_BUCKET_NAME`, `AWS_REGION` | Phase 4 category storage |
| `FLASK_ENV` | **Legacy name** — switches local vs production email/session behavior |
| Microsoft + OpenAI secrets | Backend only |

## Two S3 buckets (do not confuse)

1. **Frontend static bucket** — React `build/` artifacts; private; CloudFront OAC only (`infra/frontend.tf`).
2. **Category data bucket** — `categories/<session-id>/categories.csv` via `S3CategoryStore` (backend env).

## Local development

See [`docs/LOCAL_DEVELOPMENT.md`](docs/LOCAL_DEVELOPMENT.md).  
Root `docker-compose.yml` runs the API only; use `npm start` for the UI.

## Legacy production reference

`legacy/nginx/`, `legacy/docker-compose.production.yml` — historical `app.heilab.pitt.edu` layout.

Secrets: real `.env` files are gitignored. Only `.env.example` is tracked.

**Security:** Do not commit private keys or API secrets. A Lightsail PEM was removed from `pem/` during Phase 8 cleanup; if it was ever pushed to a remote, rotate the key and purge git history.
