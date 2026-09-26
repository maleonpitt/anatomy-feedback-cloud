# Local development (no AWS required)

The target architecture uses CloudFront + ALB in AWS, but you can run everything locally without them.

## Recommended workflow

```text
Terminal 1 — API:
  cd backend
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  FLASK_ENV=local FRONTEND_URL=http://localhost:3000 uvicorn main:app --host 0.0.0.0 --port 5001 --reload

Terminal 2 — UI:
  cd frontend
  cp .env.example .env    # REACT_APP_API_BASE_URL=http://localhost:5001
  npm install && npm start
```

Browser: `http://localhost:3000`  
API: `http://localhost:5001`  
CORS: backend allows `http://localhost:3000` when `FRONTEND_URL` is set (see `core/session.py`).

## Temporary auth bypass (local only)

Default: **off** (safe for public clones).

To skip the Microsoft Login page and go straight to the UI **on your machine only**:

```text
backend/.env:   FLASK_ENV=local
                SKIP_AUTH=true

frontend/.env:  REACT_APP_SKIP_AUTH=true
```

Then restart uvicorn and `npm start`. The UI calls `GET /dev-login`, which sets a session email.

**Reverse (restore Microsoft login):**

```text
SKIP_AUTH=false            # or remove from backend/.env
REACT_APP_SKIP_AUTH=false  # or remove from frontend/.env
```

Restart both processes. `/login` OAuth is unchanged and still used when skip-auth is off.

`/dev-login` returns 404 unless `FLASK_ENV=local` **and** `SKIP_AUTH=true`.  
Never set `SKIP_AUTH` on ECS/production task environment variables.

## Docker (API only)

```bash
docker compose up --build backend
```

Maps host `5001` → container `5000`. Pair with `npm start` on the frontend.

## Tests

```bash
cd backend && python -m pytest -v
```

## What is NOT used locally

- Nginx (retired from target architecture)
- CloudFront / frontend S3 bucket
- ALB / EC2

Those are modeled in `infra/` and documented in `docs/PHASE_6_ALB.md` and `docs/PHASE_7_CLOUDFRONT.md`.

## API paths

The frontend calls FastAPI routes directly on the API origin:

```text
REACT_APP_API_BASE_URL=http://localhost:5001
POST http://localhost:5001/send-feedback
```

There is **no** `/api` prefix. Legacy Nginx stripped `/api` before proxying; that behavior is retired.
