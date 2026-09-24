"""Tests for dual-origin CORS, cookie configuration, and session persistence."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from core.session import (
    cors_origins,
    get_frontend_url,
    session_middleware_kwargs,
)
from tests.conftest import (
    build_categories_workbook,
    build_student_workbook,
    set_session,
    upload_categories,
    upload_mockdata,
)


def test_cors_allows_configured_frontend_origin(client):
    response = client.options(
        "/get-session-email",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == (
        "http://localhost:8080"
    )
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallows_unknown_origin(client):
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_never_uses_wildcard_with_credentials(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin != "*"
    assert allow_origin == "http://localhost:8080"


def test_credentialed_session_request_returns_session_data(client):
    set_session(client, user_email="instructor@example.edu")
    response = client.get(
        "/get-session-email",
        headers={"Origin": "http://localhost:8080"},
    )
    assert response.status_code == 200
    assert response.json() == {"email": "instructor@example.edu"}
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_category_session_id_survives_upload_workflow(client):
    upload_categories(client, build_categories_workbook())
    mock = upload_mockdata(client, build_student_workbook())
    assert mock.status_code == 200


def test_oauth_state_survives_until_callback(client):
    from unittest.mock import patch

    with patch(
        "routers.auth.build_authorization_url",
        return_value=("https://login.microsoftonline.com/mock", "state-xyz"),
    ):
        login_resp = client.get("/login", follow_redirects=False)
    assert login_resp.status_code == 302

    with patch("routers.auth.exchange_code_for_token", return_value={"access_token": "t"}):
        with patch(
            "routers.auth.fetch_user_info",
            return_value={"mail": "user@example.edu"},
        ):
            cb = client.get("/callback?code=abc&state=state-xyz", follow_redirects=False)
    assert cb.status_code == 302
    assert client.get("/get-session-email").json()["email"] == "user@example.edu"


def test_local_session_cookie_settings(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "local")
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("SESSION_COOKIE_SAMESITE", raising=False)
    monkeypatch.delenv("SESSION_COOKIE_DOMAIN", raising=False)

    kwargs = session_middleware_kwargs("secret")
    assert kwargs["https_only"] is False
    assert kwargs["same_site"] == "lax"
    assert "domain" not in kwargs


def test_hypothetical_dual_origin_https_cookie_settings(monkeypatch):
    """Documented production-style flags for api.example.com (not deployed)."""
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("SESSION_COOKIE_SAMESITE", "none")
    monkeypatch.delenv("SESSION_COOKIE_DOMAIN", raising=False)

    kwargs = session_middleware_kwargs("secret")
    assert kwargs["https_only"] is True
    assert kwargs["same_site"] == "none"
    assert "domain" not in kwargs


def test_cors_origins_from_frontend_url(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    assert cors_origins() == ["https://app.example.com"]


def test_cors_origins_supports_extra_allowed_origins(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS", "https://app-staging.example.com,https://app.example.com"
    )
    origins = cors_origins()
    assert origins == ["https://app.example.com", "https://app-staging.example.com"]


def test_get_frontend_url_uses_env(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
    assert get_frontend_url() == "https://app.example.com"


def test_frontend_api_base_url_is_env_driven():
    """Frontend uses REACT_APP_API_BASE_URL with direct FastAPI paths (no /api prefix)."""
    from pathlib import Path

    app_js = (
        Path(__file__).resolve().parents[2] / "frontend" / "src" / "App.js"
    ).read_text()
    assert "process.env.REACT_APP_API_BASE_URL" in app_js
    assert "withCredentials: true" in app_js
    assert "/api/" not in app_js
    assert "`${API_BASE_URL}/send-feedback`" in app_js
    assert "OPENAI_API_KEY" not in app_js
    assert "MICROSOFT_CLIENT_SECRET" not in app_js

    example = (
        Path(__file__).resolve().parents[2] / "frontend" / ".env.example"
    ).read_text()
    assert "REACT_APP_API_BASE_URL" in example
    assert "no /api prefix" in example.lower() or "no `/api` prefix" in example
    assert "MICROSOFT_CLIENT_SECRET" not in example
