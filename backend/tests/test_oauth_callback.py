"""OAuth callback characterization (mocked Microsoft)."""

from unittest.mock import patch

from tests.conftest import set_session


def test_callback_establishes_session_and_redirects_to_frontend(client):
    set_session(client, oauth_state="state-abc")

    with patch(
        "routers.auth.exchange_code_for_token",
        return_value={"access_token": "tok", "token_type": "Bearer"},
    ):
        with patch(
            "routers.auth.fetch_user_info",
            return_value={"mail": "instructor@example.edu"},
        ):
            response = client.get(
                "/callback?code=abc&state=state-abc",
                follow_redirects=False,
            )

    assert response.status_code == 302
    assert response.headers["location"] == "http://localhost:8080"

    # Session should now include user_email for subsequent API calls
    me = client.get("/get-session-email")
    assert me.status_code == 200
    assert me.json() == {"email": "instructor@example.edu"}


def test_callback_azure_error_redirects_with_auth_failed(client):
    response = client.get(
        "/callback?error=access_denied&error_description=nope",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "error=auth_failed" in response.headers["location"]
