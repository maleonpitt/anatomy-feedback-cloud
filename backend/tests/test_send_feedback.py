"""Characterize /send-feedback local preview vs production Graph paths."""

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import set_session


def _auth_session(client, with_token: bool = True):
    data = {"user_email": "instructor@example.edu"}
    if with_token:
        data["oauth_token"] = {"access_token": "fake-graph-access-token"}
    set_session(client, **data)


@pytest.fixture
def feedback_body(sample_feedback_payload):
    return {
        "feedback": sample_feedback_payload,
        "test_name": "Midterm Exam 1",
        "instructor_name": "Dr. Jane Doe",
    }


def test_local_send_feedback_writes_html_preview_using_openai(
    client, feedback_body, monkeypatch, tmp_path
):
    """
    Current local behavior (FLASK_ENV=local):
    OpenAI summary → HTML file under test_emails/ (no Graph call).
    """
    monkeypatch.setenv("FLASK_ENV", "local")
    _auth_session(client)

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message={"content": "AI narrative summary."})]

    with patch(
        "services.openai_service.openai.ChatCompletion.create",
        return_value=mock_completion,
    ) as mock_ai:
        with patch("services.microsoft_graph.requests.post") as mock_post:
            response = client.post("/send-feedback", json=feedback_body)

    assert response.status_code == 200
    assert response.json() == {"message": "Feedback sent successfully"}
    mock_ai.assert_called()
    mock_post.assert_not_called()

    preview = tmp_path / "test_emails" / "student1_at_example.edu.html"
    assert preview.is_file()
    content = preview.read_text()
    assert "Midterm Exam 1" in content
    assert "Dr. Jane Doe" in content
    assert "AI narrative summary." in content


def test_production_send_feedback_posts_structured_html_to_graph(
    client, feedback_body, monkeypatch
):
    """
    Current production behavior (FLASK_ENV != local):
    structured HTML (no OpenAI) → Microsoft Graph sendMail.
    """
    monkeypatch.setenv("FLASK_ENV", "production")
    _auth_session(client)

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch("services.openai_service.openai.ChatCompletion.create") as mock_ai:
        with patch(
            "services.microsoft_graph.requests.post", return_value=mock_resp
        ) as mock_post:
            response = client.post("/send-feedback", json=feedback_body)

    assert response.status_code == 200
    assert response.json() == {"message": "Feedback sent successfully"}
    mock_ai.assert_not_called()
    mock_post.assert_called_once()

    args, kwargs = mock_post.call_args
    assert args[0] == "https://graph.microsoft.com/v1.0/me/sendMail"
    assert kwargs["headers"]["Authorization"] == "Bearer fake-graph-access-token"
    payload = kwargs["json"]
    assert payload["message"]["subject"] == "Feedback for Midterm Exam 1"
    assert payload["message"]["toRecipients"][0]["emailAddress"]["address"] == (
        "student1@example.edu"
    )
    html = payload["message"]["body"]["content"]
    assert payload["message"]["body"]["contentType"] == "HTML"
    assert "Predicted Course Grade: B" in html
    assert "Exam Score:" in html
    assert "Bones" in html
    assert "Dr. Jane Doe" in html


def test_production_send_feedback_without_access_token_skips_graph_but_returns_200(
    client, feedback_body, monkeypatch
):
    """
    Current behavior: missing oauth access token logs a warning and skips send;
    endpoint still returns overall success after the loop.
    """
    monkeypatch.setenv("FLASK_ENV", "production")
    _auth_session(client, with_token=False)

    with patch("services.microsoft_graph.requests.post") as mock_post:
        response = client.post("/send-feedback", json=feedback_body)

    assert response.status_code == 200
    assert response.json() == {"message": "Feedback sent successfully"}
    mock_post.assert_not_called()


def test_send_feedback_missing_feedback_payload_returns_400(client):
    _auth_session(client)
    response = client.post("/send-feedback", json={"test_name": "X"})
    assert response.status_code == 400
    assert response.json() == {"error": "No feedback data provided"}
