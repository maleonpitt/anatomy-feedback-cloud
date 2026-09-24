"""Characterize session/auth-related HTTP behavior (current contracts)."""

from unittest.mock import patch

from tests.conftest import set_session


def test_get_session_email_unauthenticated_returns_401(client):
    response = client.get("/get-session-email")
    assert response.status_code == 401
    assert response.json() == {"error": "User not logged in"}


def test_get_session_email_when_session_has_email(client):
    set_session(client, user_email="instructor@example.edu")

    response = client.get("/get-session-email")
    assert response.status_code == 200
    assert response.json() == {"email": "instructor@example.edu"}


def test_logout_clears_session(client):
    set_session(
        client,
        user_email="instructor@example.edu",
        oauth_token={"access_token": "fake-token"},
    )

    logout = client.get("/logout")
    assert logout.status_code == 200
    assert logout.json() == {"message": "Logged out successfully"}

    # Server instructs the browser to delete the session cookie.
    set_cookie = logout.headers.get("set-cookie", "")
    assert "feedback_session=" in set_cookie
    assert "expires=" in set_cookie.lower() or "max-age=0" in set_cookie.lower()

    # httpx TestClient does not always drop manually-seeded cookies on Max-Age=0;
    # simulate a browser honoring the deletion header.
    client.cookies.clear()

    after = client.get("/get-session-email")
    assert after.status_code == 401
    assert after.json() == {"error": "User not logged in"}


def test_send_feedback_requires_authenticated_session(client, sample_feedback_payload):
    """Current behavior: only send-feedback enforces session auth (not uploads)."""
    response = client.post(
        "/send-feedback",
        json={
            "feedback": sample_feedback_payload,
            "test_name": "Midterm",
            "instructor_name": "Dr. Test",
        },
    )
    assert response.status_code == 401
    assert response.json() == {"error": "Not authenticated"}


def test_login_redirects_to_microsoft(client):
    """Login should redirect to Azure authorize URL and store oauth_state."""
    with patch(
        "routers.auth.build_authorization_url",
        return_value=("https://login.microsoftonline.com/mock/authorize", "state-123"),
    ):
        response = client.get("/login", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == (
        "https://login.microsoftonline.com/mock/authorize"
    )
