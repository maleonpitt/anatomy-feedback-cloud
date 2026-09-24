"""
Shared fixtures for FastAPI characterization + unit tests.

Isolates filesystem side effects and prevents real .env secrets / external calls
from affecting the suite.
"""

from __future__ import annotations

import base64
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

import dotenv
import pytest
from itsdangerous import TimestampSigner
from openpyxl import Workbook
from starlette.testclient import TestClient

# Neutralize dotenv before importing the app so local .env cannot override tests.
dotenv.load_dotenv = lambda *args, **kwargs: False  # type: ignore[assignment]

_TEST_ENV = {
    "FLASK_ENV": "local",
    "CATEGORY_STORE_TYPE": "local",
    "SESSION_SECRET_KEY": "pytest-session-secret-not-for-production",
    "OPENAI_API_KEY": "sk-pytest-not-a-real-key",
    "MICROSOFT_CLIENT_ID": "pytest-client-id",
    "MICROSOFT_CLIENT_SECRET": "pytest-client-secret",
    "MICROSOFT_TENANT_ID": "pytest-tenant-id",
    "MICROSOFT_REDIRECT_URI": "http://localhost/callback",
    "FRONTEND_URL": "http://localhost:8080",
}

for _key, _value in _TEST_ENV.items():
    os.environ[_key] = _value

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from main import SECRET_KEY, app as fastapi_app  # noqa: E402


@pytest.fixture
def app():
    return fastapi_app


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _isolate_workdir(tmp_path, monkeypatch):
    """Keep categories.csv and test_emails/ out of the source tree."""
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def sample_feedback_payload():
    return {
        "student1@example.edu": {
            "score": 80,
            "predicted_grade": "B",
            "categories": [{"category": "Bones", "module": "Module A"}],
            "summary": {"Bones": 1},
            "most_work_category": "Bones",
        }
    }


def encode_session_cookie(data: dict[str, Any], secret_key: str = SECRET_KEY) -> str:
    """Create a Starlette SessionMiddleware-compatible cookie value."""
    signer = TimestampSigner(str(secret_key))
    payload = base64.b64encode(json.dumps(data).encode("utf-8"))
    return signer.sign(payload).decode("utf-8")


def set_session(client: TestClient, **data: Any) -> None:
    """
    Establish session state the way SessionMiddleware does in production:
    issue a signed cookie and ensure the TestClient jar will replace/clear it
    correctly on Set-Cookie (path=/).
    """
    client.cookies.set("feedback_session", encode_session_cookie(data), path="/")


def build_categories_workbook(
    rows: list[tuple] | None = None,
    headers: list[str] | None = None,
) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(
        headers or ["Question Id", "Category", "Module", "Question Title"]
    )
    if rows is None:
        rows = [
            ("Q1", "Bones", "Module A", "Femur question"),
            ("Q2", "Muscles", "Module B", "Bicep question"),
        ]
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_student_workbook(
    rows: list[tuple] | None = None,
    headers: list[str] | None = None,
) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(
        headers
        or [
            "Participant Number",
            "Email",
            "score",
            "Predicted Grade",
            "Q1",
            "Q2",
            "Q999",
        ]
    )
    if rows is None:
        rows = [
            (1, "student1@example.edu", 80, "B", 0, 1, 0),
        ]
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def categories_xlsx_bytes():
    return build_categories_workbook()


@pytest.fixture
def student_xlsx_bytes():
    return build_student_workbook()


def upload_categories(client, xlsx_bytes: bytes, filename: str = "categories.xlsx"):
    return client.post(
        "/upload-categories",
        files={
            "file": (
                filename,
                io.BytesIO(xlsx_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )


def upload_mockdata(client, xlsx_bytes: bytes, filename: str = "students.xlsx"):
    return client.post(
        "/upload-mockdata",
        files={
            "file": (
                filename,
                io.BytesIO(xlsx_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
