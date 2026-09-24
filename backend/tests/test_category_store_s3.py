"""Unit tests for S3CategoryStore (mocked boto3 — no real AWS calls)."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from botocore.exceptions import ClientError

from services.category_store import (
    CategoryNotFoundError,
    CategoryStoreError,
    CategoryStorePermissionError,
    S3CategoryStore,
    get_category_store,
    object_key,
)

SAMPLE_DF = pd.DataFrame(
    [
        {
            "Question Id": "Q1",
            "Category": "Bones",
            "Module": "A",
            "Question Title": "t",
        }
    ]
)


def _client_error(code: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": "test"}},
        "GetObject",
    )


@pytest.fixture
def mock_s3():
    return MagicMock()


@pytest.fixture
def store(mock_s3):
    return S3CategoryStore(bucket="test-bucket", region="us-east-1", client=mock_s3)


def test_save_puts_object_at_session_scoped_key(store, mock_s3):
    store.save(SAMPLE_DF, "uuid-123")

    mock_s3.put_object.assert_called_once()
    kwargs = mock_s3.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "test-bucket"
    assert kwargs["Key"] == object_key("uuid-123")
    assert kwargs["ContentType"] == "text/csv"
    assert b"Question Id" in kwargs["Body"]


def test_load_reads_object_from_session_scoped_key(store, mock_s3):
    buffer = io.StringIO()
    SAMPLE_DF.to_csv(buffer, index=False)
    mock_s3.get_object.return_value = {
        "Body": io.BytesIO(buffer.getvalue().encode("utf-8"))
    }

    loaded = store.load("uuid-456")
    mock_s3.get_object.assert_called_once_with(
        Bucket="test-bucket", Key=object_key("uuid-456")
    )
    assert loaded.iloc[0]["Question Id"] == "Q1"


def test_load_missing_object_raises_category_not_found(store, mock_s3):
    mock_s3.get_object.side_effect = _client_error("NoSuchKey")
    with pytest.raises(CategoryNotFoundError):
        store.load("missing")


def test_load_permission_denied_raises(store, mock_s3):
    mock_s3.get_object.side_effect = _client_error("AccessDenied")
    with pytest.raises(CategoryStorePermissionError):
        store.load("uuid-123")


def test_save_s3_error_propagates(store, mock_s3):
    mock_s3.put_object.side_effect = _client_error("ServiceUnavailable")
    with pytest.raises(CategoryStoreError):
        store.save(SAMPLE_DF, "uuid-123")


def test_two_sessions_use_distinct_keys(store, mock_s3):
    store.save(SAMPLE_DF, "session-a")
    store.save(SAMPLE_DF, "session-b")

    keys = [call.kwargs["Key"] for call in mock_s3.put_object.call_args_list]
    assert object_key("session-a") in keys
    assert object_key("session-b") in keys
    assert keys[0] != keys[1]


def test_get_category_store_s3_requires_bucket(monkeypatch):
    monkeypatch.setenv("CATEGORY_STORE_TYPE", "s3")
    monkeypatch.delenv("CATEGORY_BUCKET_NAME", raising=False)
    with pytest.raises(CategoryStoreError, match="CATEGORY_BUCKET_NAME"):
        get_category_store()


def test_get_category_store_s3_returns_s3_store(monkeypatch):
    monkeypatch.setenv("CATEGORY_STORE_TYPE", "s3")
    monkeypatch.setenv("CATEGORY_BUCKET_NAME", "my-bucket")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    with patch("services.category_store.boto3.client") as mock_client:
        mock_client.return_value = MagicMock()
        store = get_category_store()
    assert isinstance(store, S3CategoryStore)
    assert store.bucket == "my-bucket"
