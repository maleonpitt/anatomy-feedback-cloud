"""Session-scoped identifier for category storage (opaque, not PII)."""

from __future__ import annotations

import uuid
from typing import Any

CATEGORY_SESSION_KEY = "category_session_id"


def get_or_create_category_session_id(session: dict[str, Any]) -> str:
    """
    Return the opaque id used to locate this browser's category data in storage.

    Created on first category upload; reused for subsequent mockdata upload
  in the same signed session cookie.
    """
    existing = session.get(CATEGORY_SESSION_KEY)
    if existing:
        return str(existing)
    session_id = str(uuid.uuid4())
    session[CATEGORY_SESSION_KEY] = session_id
    return session_id


def get_category_session_id(session: dict[str, Any]) -> str | None:
    """Return session id if categories were uploaded; else None."""
    value = session.get(CATEGORY_SESSION_KEY)
    return str(value) if value else None
