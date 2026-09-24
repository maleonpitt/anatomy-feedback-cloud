"""
CORS, session cookie, and frontend-origin configuration.

Supports:
  - same-origin local dev (CRA :3000 + API :5001)
  - dual-origin (e.g. https://app.example.com UI, https://api.example.com API)

See docs/DUAL_ORIGIN.md for cookie SameSite / same-site vs cross-origin notes.
"""

from __future__ import annotations

import os


def flask_env() -> str:
    return os.getenv("FLASK_ENV", "production").lower()


def is_local_env() -> bool:
    return flask_env() == "local"


def get_frontend_url() -> str:
    """
    Frontend origin used for OAuth redirects (FRONTEND_URL).

    No trailing slash. Required in non-local environments.
    """
    url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
    if url:
        return url
    if is_local_env():
        return "http://localhost:3000"
    raise RuntimeError(
        "FRONTEND_URL must be set when FLASK_ENV is not local "
        "(e.g. https://app.example.com)"
    )


def cors_origins() -> list[str]:
    """
    Explicit CORS allowlist for credentialed browser requests.

    Never returns wildcard (*). Primary source: FRONTEND_URL.
    Optional extras: CORS_ALLOWED_ORIGINS (comma-separated).
    """
    origins: list[str] = []

    frontend = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
    if frontend:
        origins.append(frontend)

    extra = os.getenv("CORS_ALLOWED_ORIGINS", "")
    for origin in extra.split(","):
        origin = origin.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)

    if origins:
        return origins

    if is_local_env():
        return [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ]

    raise RuntimeError(
        "Set FRONTEND_URL and/or CORS_ALLOWED_ORIGINS for CORS in non-local environments"
    )


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def session_middleware_kwargs(secret_key: str) -> dict:
    """
    Starlette SessionMiddleware settings for feedback_session.

    Environment overrides (all optional):
      SESSION_COOKIE_SECURE   — default false in local, true otherwise
      SESSION_COOKIE_SAMESITE — lax | none | strict
      SESSION_COOKIE_DOMAIN   — omit for host-only API cookie (recommended
                                for dual-origin api.example.com)

    Local defaults: Secure=false, SameSite=lax, no Domain.
    Non-local defaults: Secure=true, SameSite=none, no Domain unless set.

    SameSite=none requires Secure=true (enforced by browsers).
    """
    local = is_local_env()
    secure = _parse_bool(os.getenv("SESSION_COOKIE_SECURE"), default=not local)

    same_site_raw = os.getenv("SESSION_COOKIE_SAMESITE", "").strip().lower()
    if same_site_raw:
        same_site = same_site_raw
    else:
        same_site = "lax" if local else "none"

    if same_site == "none" and not secure:
        secure = True

    kwargs: dict = {
        "secret_key": secret_key,
        "session_cookie": "feedback_session",
        "https_only": secure,
        "same_site": same_site,
    }

    domain = os.getenv("SESSION_COOKIE_DOMAIN", "").strip()
    if domain:
        kwargs["domain"] = domain

    return kwargs
