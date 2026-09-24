# Phase 7 — CloudFront + S3 frontend (local design)

This document describes the **hypothetical** dual-origin target architecture. Nothing here is deployed to AWS or the live site.

## Complete target architecture

```text
                     Internet
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ↓                           ↓
     CloudFront                      ALB :443
     (app.example.com)               (api.example.com)
          ↓                           ↓
     Private S3                 Target Group
     (React build)                    ↓
          ↓                      EC2-A / EC2-B
     React SPA                         ↓
                                   Docker
                                      ↓
                                   Uvicorn :5000
                                      ↓
                                   FastAPI
                                      ↓
                                   services
                                      ↓
                          Category S3 (Phase 4)
```

**Nginx is not part of this model.**

## Two S3 buckets

| Bucket | Purpose | Access |
|--------|---------|--------|
| Frontend static (`frontend_bucket_name`) | `npm run build` output (`index.html`, JS, CSS) | Private; **only** CloudFront via OAC |
| Category data (`CATEGORY_BUCKET_NAME`) | `categories/<category_session_id>/categories.csv` | Backend IAM role on EC2; not browser-facing |

Do not serve the React app from the category bucket or vice versa.

## Nginx responsibility migration

| Former Nginx role | New owner |
|-------------------|-----------|
| TLS for frontend | CloudFront + ACM (`frontend_certificate_arn`) |
| Serve React static files | Private S3 + CloudFront |
| SPA fallback (`try_files`, 404 → `index.html`) | CloudFront `custom_error_response` 403/404 → `/index.html` with 200 |
| Security headers (HSTS, X-Frame-Options, etc.) | CloudFront `response_headers_policy` |
| API reverse proxy | ALB → target group (Phase 6) |
| Backend TLS termination | ALB HTTPS listener |
| `/api` prefix strip | **Retired** — frontend uses explicit API paths on `api.example.com` |

Legacy Nginx config is archived under [`legacy/nginx/`](../legacy/nginx/).

## Frontend request path

```text
Browser
   ↓ HTTPS
CloudFront distribution
   ↓ OAC (SigV4)
Private S3 bucket
   ↓ object key (e.g. index.html, static/js/*.js)
React application
```

Build pipeline (conceptual):

```text
frontend/ → npm run build → build/ → sync to S3 → CloudFront invalidation (real deploy only)
```

## SPA routing (e.g. `/dashboard`)

The app is currently a single-page shell without React Router routes, but client-side routing is supported by the target infra:

1. Browser requests `https://app.example.com/dashboard`
2. S3 has no object at `/dashboard` → 403/404
3. CloudFront `custom_error_response` returns `/index.html` with HTTP 200
4. React boots and the client router handles `/dashboard`

This replaces Nginx:

```nginx
try_files $uri $uri/ /index.html;
error_page 404 /index.html;
```

## Backend request path

```text
Browser
   ↓ HTTPS + feedback_session cookie
ALB :443 (TLS termination)
   ↓ HTTP
Target Group → healthy EC2
   ↓
Uvicorn 0.0.0.0:5000
   ↓
FastAPI (/send-feedback, /login, …)
   ↓
S3CategoryStore / Graph / OpenAI
```

CloudFront does **not** proxy API traffic in this model.

## `/api` path retirement

**Before (Nginx same-origin):**

```text
Browser:  POST https://app.heilab.pitt.edu/api/send-feedback
Nginx:    strip /api → proxy to backend
FastAPI:  POST /send-feedback
```

**After (dual-origin, no Nginx):**

```text
REACT_APP_API_BASE_URL=https://api.example.com
Browser:  POST https://api.example.com/send-feedback
FastAPI:  POST /send-feedback
```

Frontend `App.js` was updated in Phase 7 to drop the `/api` prefix. Backend routes are unchanged.

## Frontend API configuration

| Environment | `REACT_APP_API_BASE_URL` |
|-------------|--------------------------|
| Local | `http://localhost:5001` |
| Hypothetical prod | `https://api.example.com` |

Set at **build time** (CRA). No hardcoded live domains in source.

## Session across origins

```text
https://app.example.com  (UI, CloudFront)
https://api.example.com  (API, ALB)
```

Signed `feedback_session` cookie on the API host; CORS + `withCredentials: true`.  
Multi-instance categories via `category_session_id` + shared category S3 — **no sticky sessions**.

## Terraform model

See [`infra/frontend.tf`](../infra/frontend.tf):

- `aws_s3_bucket` + `public_access_block` (all blocked)
- `aws_cloudfront_origin_access_control`
- `aws_cloudfront_distribution` with SPA error responses
- `aws_s3_bucket_policy` allowing CloudFront service principal only

Phase 6 API resources remain in [`infra/main.tf`](../infra/main.tf).

## Local development

See [`LOCAL_DEVELOPMENT.md`](LOCAL_DEVELOPMENT.md).  
CRA dev server + Uvicorn; no AWS, no Nginx.

## What was not done (requires real AWS)

- S3 bucket creation or `aws s3 sync` of build artifacts
- CloudFront distribution deployment
- ACM certificate issuance / DNS validation
- Route 53 alias records
- Cache invalidation
- Live Nginx removal on production server

**No live site or real AWS resources were accessed, modified, created, queried, uploaded to, invalidated, or deployed for Phase 7.**
