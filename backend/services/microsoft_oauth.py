"""Microsoft OAuth helpers (Azure AD authorize / token exchange)."""

from __future__ import annotations

from typing import Any

from requests_oauthlib import OAuth2Session

SCOPES = ["User.Read", "Mail.Send"]


def token_url(tenant_id: str) -> str:
    return f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


def auth_base_url(tenant_id: str) -> str:
    return f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"


def build_authorization_url(
    client_id: str, redirect_uri: str, tenant_id: str
) -> tuple[str, str]:
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=SCOPES)
    return oauth.authorization_url(auth_base_url(tenant_id), prompt="select_account")


def exchange_code_for_token(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    tenant_id: str,
    state: str | None,
    authorization_response: str,
) -> dict[str, Any]:
    oauth = OAuth2Session(client_id, state=state, redirect_uri=redirect_uri)
    return oauth.fetch_token(
        token_url(tenant_id),
        client_secret=client_secret,
        authorization_response=authorization_response,
    )


def fetch_user_info(client_id: str, token: dict[str, Any]) -> dict[str, Any]:
    oauth = OAuth2Session(client_id, token=token)
    return oauth.get("https://graph.microsoft.com/v1.0/me").json()
