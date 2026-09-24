"""Local SKIP_AUTH /dev-login bypass (reversible; production stays OAuth-only)."""

from __future__ import annotations


def test_dev_login_disabled_by_default(client):
    """Without SKIP_AUTH, /dev-login is not available (404)."""
    response = client.get("/dev-login")
    assert response.status_code == 404


def test_dev_login_requires_local_env(client, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SKIP_AUTH", "true")
    response = client.get("/dev-login")
    assert response.status_code == 404


def test_dev_login_sets_session_when_enabled(client, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "local")
    monkeypatch.setenv("SKIP_AUTH", "true")
    monkeypatch.setenv("DEV_LOGIN_EMAIL", "dev@example.com")

    response = client.get("/dev-login")
    assert response.status_code == 200
    assert response.json() == {"email": "dev@example.com", "dev_login": True}

    me = client.get("/get-session-email")
    assert me.status_code == 200
    assert me.json() == {"email": "dev@example.com"}


def test_frontend_skip_auth_is_env_driven():
    from pathlib import Path

    app_js = (
        Path(__file__).resolve().parents[2] / "frontend" / "src" / "App.js"
    ).read_text()
    assert "REACT_APP_SKIP_AUTH" in app_js
    assert "/dev-login" in app_js
