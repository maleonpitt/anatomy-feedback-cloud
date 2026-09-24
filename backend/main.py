"""
FastAPI application entrypoint.

Dual-origin target: ALB terminates TLS and forwards HTTP to Uvicorn on :5000.
Frontend is served separately via CloudFront → S3 (Phase 7).
Business logic remains in services/ (Phase 2).
"""

from __future__ import annotations

import logging
import os

import openai
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from core.session import cors_origins, session_middleware_kwargs
from routers import auth, feedback, health, uploads

load_dotenv(find_dotenv(".env"), override=True)

print(f"🧭 Using redirect URI: {os.getenv('MICROSOFT_REDIRECT_URI')}")
print(f"🌎 FLASK_ENV: {os.getenv('FLASK_ENV')}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

SECRET_KEY = os.getenv("SESSION_SECRET_KEY") or os.urandom(24).hex()

app = FastAPI(title="Anatomy Feedback API", docs_url=None, redoc_url=None)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Route accessed: {request.method} {request.url.path}")
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, **session_middleware_kwargs(SECRET_KEY))
# Outermost: honor X-Forwarded-* from ALB or other reverse proxies.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(feedback.router)
app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=False)
