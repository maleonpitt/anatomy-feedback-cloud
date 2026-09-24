"""Unit tests for structured email rendering and Graph payload construction."""

from unittest.mock import MagicMock, patch

from services.email_renderer import build_email_subject, render_structured_email_html
from services.microsoft_graph import build_send_mail_payload, send_mail


SAMPLE_FEEDBACK = {
    "score": 80,
    "predicted_grade": "B",
    "categories": [{"category": "Bones", "module": "Module A"}],
    "summary": {"Bones": 1},
    "most_work_category": "Bones",
}


def test_build_email_subject_with_and_without_test_name():
    assert build_email_subject("Midterm") == "Feedback for Midterm"
    assert build_email_subject("") == "Your Feedback from the Last Assessment"
    assert build_email_subject(None) == "Your Feedback from the Last Assessment"


def test_render_structured_email_html_contains_card_fields():
    html = render_structured_email_html(SAMPLE_FEEDBACK, instructor_name="Dr. Jane Doe")
    assert "Predicted Course Grade: B" in html
    assert "Exam Score:" in html
    assert "80" in html
    assert "Bones: 1 wrong" in html
    assert "Bones: Module A" in html
    assert "Needs Most Work:</strong> Bones" in html
    assert "Dr. Jane Doe" in html


def test_build_send_mail_payload_shape():
    payload = build_send_mail_payload(
        "student@example.edu", "Feedback for Midterm", "<p>hi</p>"
    )
    assert payload["message"]["subject"] == "Feedback for Midterm"
    assert payload["message"]["body"]["contentType"] == "HTML"
    assert payload["message"]["body"]["content"] == "<p>hi</p>"
    assert payload["message"]["toRecipients"][0]["emailAddress"]["address"] == (
        "student@example.edu"
    )


def test_send_mail_posts_to_graph_and_propagates_success():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    with patch("services.microsoft_graph.requests.post", return_value=mock_resp) as mock_post:
        send_mail("tok", "s@ex.edu", "Subj", "<html/>")

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://graph.microsoft.com/v1.0/me/sendMail"
    assert kwargs["headers"]["Authorization"] == "Bearer tok"
    mock_resp.raise_for_status.assert_called_once()


def test_send_mail_logs_http_error_without_raising():
    from requests.exceptions import HTTPError

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = HTTPError("boom")
    with patch("services.microsoft_graph.requests.post", return_value=mock_resp):
        # Historical behavior: catch HTTPError inside send_mail, do not raise.
        send_mail("tok", "s@ex.edu", "Subj", "<html/>")
