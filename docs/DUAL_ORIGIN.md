# Dual-origin frontend / API architecture (Phase 5)

This document describes how the **local codebase** supports a hypothetical split deployment. Nothing here is deployed or validated against a live environment.

## Target architecture (hypothetical)

```text
Browser
   │
   ├── Frontend: https://app.example.com   (React / CloudFront + S3, future)
   │
   └── API:      https://api.example.com   (FastAPI / ALB, future)
```

Today locally you can simulate this with:

```text
FRONTEND_URL=http://localhost:3000
REACT_APP_API_BASE_URL=http://localhost:5001
```

## Cross-origin vs same-site

| Pair | Cross-origin? | Same-site? |
|------|---------------|------------|
| `https://app.example.com` → `https://api.example.com` | **Yes** (different host) | **Yes** (same registrable domain `example.com`) |
| `http://localhost:3000` → `http://localhost:5001` | **Yes** (different port) | **Yes** (`localhost`) |
| `https://app.example.com` → `https://evil.com` | Yes | **No** (cross-site) |

- **CORS** applies because the browser treats these as **different origins**. The API must explicitly allow the frontend origin (`FRONTEND_URL`) with `allow_credentials=True`. Wildcard `*` is **not** used with credentials.
- **Cookies** are set on the **API host** (`api.example.com`). The React app never reads the session cookie in JavaScript; Axios sends it via `withCredentials: true`.

## SameSite guidance (not automatic)

Do **not** assume “different origin ⇒ SameSite=None” in every case.

- **Same-site, cross-origin** (e.g. `app.example.com` ↔ `api.example.com`): modern browsers often send `SameSite=Lax` cookies on same-site subresource requests. Many dual-subdomain setups use `SameSite=None; Secure` for maximum compatibility with credentialed XHR/fetch—configure explicitly if needed.
- **Cross-site** (different registrable domains): requires `SameSite=None; Secure` and strict CORS.
- **Local HTTP** (`localhost`): `Secure=false`, `SameSite=lax` (defaults in code when `FLASK_ENV=local`).

Configure via:

```text
SESSION_COOKIE_SECURE=true|false
SESSION_COOKIE_SAMESITE=lax|none|strict
SESSION_COOKIE_DOMAIN=          # usually unset (host-only on API); avoid legacy shared-domain hacks unless required
```

## OAuth (environment-driven only)

```text
User on frontend → navigates to API /login
  → Microsoft → API /callback (MICROSOFT_REDIRECT_URI on API host)
  → session cookie set on API host
  → redirect to FRONTEND_URL
```

Future Azure app registration would need `MICROSOFT_REDIRECT_URI=https://api.example.com/callback` (document only—not changed in this repo).

## Environment variables

| Variable | Role |
|----------|------|
| `FRONTEND_URL` | CORS allowlist primary origin; OAuth redirect target |
| `CORS_ALLOWED_ORIGINS` | Optional comma-separated extra origins |
| `REACT_APP_API_BASE_URL` | Frontend build: API origin (e.g. `https://api.example.com`) |
| `MICROSOFT_REDIRECT_URI` | OAuth callback on **API** host |
| `SESSION_COOKIE_*` | Cookie flags for local vs hypothetical HTTPS dual-origin |

## What Phase 5 validates locally

- CORS allow/deny and preflight (TestClient)
- Session cookie flags from configuration
- Session persistence (`category_session_id`, OAuth state) across requests
- No wildcard credentialed CORS
- Config-driven origins (no hardcoded live domains in application code)

## What requires real infrastructure (not done in this repo)

- Real DNS, ACM certificates, ALB, CloudFront
- Browser testing on real `app.example.com` / `api.example.com`
- Azure redirect URI registration updates
- IAM / S3 / production cookie behavior on HTTPS

## API paths (Phase 7)

The target architecture uses **direct FastAPI routes** on the API origin — no `/api` prefix.

```text
REACT_APP_API_BASE_URL=https://api.example.com
POST https://api.example.com/send-feedback  →  FastAPI POST /send-feedback
```

Legacy Nginx stripped `/api` before proxying; that behavior is retired. See `docs/PHASE_7_CLOUDFRONT.md`.
