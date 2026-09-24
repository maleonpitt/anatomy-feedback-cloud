"""Auth / OAuth / session routes."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from services.microsoft_graph import extract_user_email
from services.microsoft_oauth import (
    build_authorization_url,
    exchange_code_for_token,
    fetch_user_info,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")
from core.session import get_frontend_url, is_local_env


def _dev_login_enabled() -> bool:
    """Local-only bypass. Requires FLASK_ENV=local and SKIP_AUTH=true."""
    return is_local_env() and os.getenv("SKIP_AUTH", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


@router.get("/dev-login")
async def dev_login(request: Request):
    """
    Temporary local auth bypass (Option B).

    Sets a session so the UI and /send-feedback work without Microsoft OAuth.
    Reverse: unset SKIP_AUTH (or set false) and restart; OAuth /login is unchanged.
    """
    if not _dev_login_enabled():
        return JSONResponse(
            {"error": "dev-login disabled (requires FLASK_ENV=local and SKIP_AUTH=true)"},
            status_code=404,
        )

    email = (
        os.getenv("DEV_LOGIN_EMAIL", "").strip() or "local-dev@example.com"
    )
    request.session["user_email"] = email
    # No real Graph token — local send-feedback uses HTML preview path.
    request.session.pop("oauth_token", None)
    logger.warning("DEV LOGIN active for %s (SKIP_AUTH=true)", email)
    return JSONResponse({"email": email, "dev_login": True}, status_code=200)


@router.get("/login")
async def login(request: Request):
    try:
        auth_url, state = build_authorization_url(CLIENT_ID, REDIRECT_URI, TENANT_ID)
        request.session["oauth_state"] = state
        return RedirectResponse(url=auth_url, status_code=302)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JSONResponse({"error": "Login failed"}, status_code=500)


@router.get("/callback")
async def callback(request: Request):
    try:
        if "error" in request.query_params:
            logger.error(
                f"Azure returned error: {request.query_params.get('error_description')}"
            )
            return RedirectResponse(
                url=f"{get_frontend_url()}/?error=auth_failed", status_code=302
            )

        logger.info(f"OAuth redirect: {REDIRECT_URI} (env={os.getenv('FLASK_ENV', 'production')})")
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = (
            "1" if os.getenv("FLASK_ENV", "production").lower() == "local" else "0"
        )

        token = exchange_code_for_token(
            CLIENT_ID,
            CLIENT_SECRET,
            REDIRECT_URI,
            TENANT_ID,
            request.session.get("oauth_state"),
            str(request.url),
        )
        request.session["oauth_token"] = token
        logger.info("✅ Token successfully fetched from Azure.")

        user_info = fetch_user_info(CLIENT_ID, token)
        logger.info(f"👤 Microsoft Graph response: {user_info}")

        user_email = extract_user_email(user_info)
        if not user_email:
            raise ValueError("Could not extract user email from Graph API response.")

        request.session["user_email"] = user_email
        logger.info(f"✅ User logged in: {user_email}")

        return RedirectResponse(url=get_frontend_url(), status_code=302)

    except Exception as e:
        logger.error(f"Callback error: {str(e)}", exc_info=True)
        return RedirectResponse(
            url=f"{get_frontend_url()}/?error=auth_failed", status_code=302
        )


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse({"message": "Logged out successfully"}, status_code=200)


@router.get("/get-session-email")
async def get_session_email(request: Request):
    user_email = request.session.get("user_email")
    if user_email:
        return JSONResponse({"email": user_email}, status_code=200)
    return JSONResponse({"error": "User not logged in"}, status_code=401)
