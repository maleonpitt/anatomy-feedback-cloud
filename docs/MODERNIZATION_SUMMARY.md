# Modernization summary (Phases 0–8)

Local agentic-engineering exercise modernizing the anatomy-feedback application.  
**Nothing in this repository proves that AWS infrastructure was deployed or validated in a real account.**

## Before

```text
Browser
   ↓
Nginx (TLS + reverse proxy)
   ├── serves React static build
   └── proxies /api/* → backend
         ↓
      Flask / Gunicorn
         ↓
      local categories.csv (global on disk)
```

## After / target model

```text
                     Browser
                        │
          ┌─────────────┴─────────────┐
          ↓                           ↓
     CloudFront                      ALB
          ↓                           ↓
   Private frontend S3          Target Group
          ↓                      /        \
      React SPA                 EC2-A      EC2-B
                                    ↓          ↓
                                 Docker      Docker
                                    ↓          ↓
                                 Uvicorn    Uvicorn
                                    ↓          ↓
                                 FastAPI    FastAPI
                                     \        /
                                      \      /
                              Shared category S3
```

## Implemented locally vs modeled in AWS

| Area | Implemented locally | Modeled only (Terraform/docs) |
|------|---------------------|-------------------------------|
| FastAPI + Uvicorn | Yes | EC2 hosts in `infra/main.tf` |
| Service layer + S3 store | Yes | Category bucket IAM (documented) |
| pytest suite (76 tests) | Yes | — |
| React build | Yes | S3 sync / invalidation |
| CORS / session cookies | Yes | Production cookie domains |
| CloudFront + frontend S3 | — | `infra/frontend.tf` |
| ALB + target group | — | `infra/main.tf` |
| DNS, ACM, Route 53 | — | Placeholder variables |

## Major decisions

1. **Phase 0 — Characterization tests** before refactoring Flask behavior.
2. **Phase 1 — Config hygiene** — secrets out of frontend; `.env.example` files.
3. **Phase 2 — Service extraction** from Flask monolith into `backend/services/`.
4. **Phase 3 — FastAPI + Uvicorn** replacing Flask/Gunicorn; routers + session middleware.
5. **Phase 4 — S3 category store** — `CategoryStore` abstraction; session-scoped `category_session_id`; keys `categories/<uuid>/categories.csv`.
6. **Phase 5 — Dual-origin prep** — `FRONTEND_URL`, CORS, cookie flags; `REACT_APP_API_BASE_URL`.
7. **Phase 6 — ALB model** — public ALB, private EC2, security groups, `/health` target checks.
8. **Phase 7 — CloudFront model** — private frontend S3, OAC, SPA fallback; Nginx retired from target arch; explicit API paths (no `/api` strip).
9. **Phase 8 — Repository cleanup** — legacy separation, docs, validation.

## Two S3 buckets (do not combine)

| Bucket | Contents | Access |
|--------|----------|--------|
| Frontend static | `npm run build` output | CloudFront OAC only |
| Category data | `categories/<session-id>/categories.csv` | Backend IAM on EC2 |

## API path change (Nginx retirement)

| Era | Browser calls | Backend receives |
|-----|---------------|------------------|
| Legacy Nginx same-origin | `POST /api/send-feedback` | `POST /send-feedback` (strip) |
| Target dual-origin | `POST https://api.example.com/send-feedback` | `POST /send-feedback` |

Frontend `App.js` uses direct FastAPI paths with `REACT_APP_API_BASE_URL`.

## Legacy material

| Location | Contents |
|----------|----------|
| `legacy/nginx/` | Historical Nginx + Let's Encrypt config |
| `legacy/docker-compose.production.yml` | Live-server reference layout |
| `../anatomy-feedback-backup/` | Pre-modernization snapshot (Flask monolith) |

All marked **LEGACY / REFERENCE ONLY — NOT PART OF TARGET ARCHITECTURE — DO NOT DEPLOY**.

## Backup comparison (Phase 8)

`anatomy-feedback-backup/` is a near-duplicate of the **pre-modernization** tree:

- Contains `backend/app.py` (Flask monolith) — removed from canonical repo
- No `routers/`, `services/`, `tests/`, `infra/`, `docs/`, `legacy/`
- Active `nginx/` at repo root (not archived)
- No FastAPI migration artifacts

**Nothing unique is required** for the modernized application. The backup is retained only as a historical reference until manually removed.

## Configuration reference

See [`CONFIG.md`](../CONFIG.md) and [`DUAL_ORIGIN.md`](DUAL_ORIGIN.md).

`FLASK_ENV` remains the environment switch name (historical label) for local vs production email/session behavior.

## Validation performed in Phase 8

- `python -m pytest` — 76 tests
- `npm run build` — frontend production build
- `terraform fmt` / `terraform validate` — infra model (local only)

## Not performed

- AWS deploy, `terraform apply`, live server changes
- Secret rotation (see security note in Phase 8 report if local `.env` or committed keys found)

**No live site or real AWS resources were accessed, modified, created, queried, uploaded to, invalidated, destroyed, or deployed.**
