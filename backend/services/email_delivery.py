"""
Email delivery orchestration.

Preserves Phase 0 / historical behavior:
  local      → OpenAI narrative → simple HTML file under test_emails/
  production → structured HTML → Microsoft Graph sendMail
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from services.email_renderer import build_email_subject, render_structured_email_html
from services.microsoft_graph import send_mail
from services.openai_service import generate_feedback_summary

logger = logging.getLogger(__name__)


def _coerce_feedback(student_email: str, feedback: Any) -> dict[str, Any] | None:
    if isinstance(feedback, str):
        try:
            feedback = json.loads(feedback)
        except Exception:
            logger.warning(
                f"Skipping {student_email}: feedback is not valid JSON string."
            )
            return None

    if not isinstance(feedback, dict):
        logger.warning(
            f"Skipping {student_email}: invalid feedback format ({type(feedback).__name__})"
        )
        return None

    return feedback


def deliver_student_feedback(
    student_email: str,
    feedback: Any,
    test_name: str | None = None,
    instructor_name: str | None = None,
    *,
    flask_env: str | None = None,
    access_token: str | None = None,
) -> None:
    """
    Deliver one student's feedback according to environment.

    access_token is required for production Graph delivery; routes pass
    it from the session (keeps this module free of web framework imports).
    """
    feedback = _coerce_feedback(student_email, feedback)
    if feedback is None:
        return

    env = (flask_env if flask_env is not None else os.getenv("FLASK_ENV", "")).lower()

    if env == "local":
        summary = generate_feedback_summary(feedback)
        preview_path = os.path.join(os.getcwd(), "test_emails")
        os.makedirs(preview_path, exist_ok=True)
        file_path = os.path.join(
            preview_path, f"{student_email.replace('@', '_at_')}.html"
        )

        with open(file_path, "w") as f:
            f.write(f"<h2>Subject: Feedback for {test_name or 'Test'}</h2>\n")
            f.write(
                f"<p><strong>Instructor:</strong> {instructor_name or 'Instructor'}</p>\n"
            )
            f.write(summary.replace("\n", "<br>"))

        logger.info(f"[LOCAL MODE] Saved test email preview: {file_path}")
        return

    # Production path
    if not access_token:
        logger.warning("Missing access token.")
        return

    subject = build_email_subject(test_name)
    email_body = render_structured_email_html(feedback, instructor_name)
    send_mail(access_token, student_email, subject, email_body)
