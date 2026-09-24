"""Microsoft Graph HTTP helpers (non-Flask)."""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

GRAPH_SEND_MAIL_URL = "https://graph.microsoft.com/v1.0/me/sendMail"
GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"


def build_send_mail_payload(
    student_email: str, subject: str, html_body: str
) -> dict[str, Any]:
    return {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": student_email}}],
        }
    }


def send_mail(
    access_token: str, student_email: str, subject: str, html_body: str
) -> None:
    """
    POST /me/sendMail. Raises HTTPError on non-success (caller may catch).

    Matches historical app.py behavior: log HTTPError and let caller decide.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    email_data = build_send_mail_payload(student_email, subject, html_body)

    try:
        response = requests.post(
            GRAPH_SEND_MAIL_URL,
            headers=headers,
            json=email_data,
        )
        response.raise_for_status()
        logger.info(f"Feedback email sent to {student_email}")
    except HTTPError as e:
        logger.error(f"Failed to send email to {student_email}: {str(e)}")


def extract_user_email(user_info: dict[str, Any]) -> str | None:
    return (
        user_info.get("mail")
        or user_info.get("userPrincipalName")
        or user_info.get("id")
    )
