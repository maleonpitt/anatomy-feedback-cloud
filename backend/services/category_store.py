"""Category persistence — local filesystem or S3 (session-scoped keys)."""

from __future__ import annotations

import io
import logging
import os
from abc import ABC, abstractmethod

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

CATEGORY_KEY_FILENAME = "categories.csv"
CATEGORY_KEY_PREFIX = "categories"


class CategoryStoreError(Exception):
    """Base error for category persistence failures."""


class CategoryNotFoundError(CategoryStoreError):
    """No category data exists for the given session."""


class CategoryStorePermissionError(CategoryStoreError):
    """Insufficient permissions to access category storage."""


class CategoryStore(ABC):
    """Contract for reading/writing category tables keyed by session id."""

    @abstractmethod
    def save(self, df: pd.DataFrame, session_id: str) -> None:
        """Persist category data for a session."""

    @abstractmethod
    def load(self, session_id: str) -> pd.DataFrame:
        """Load category data for a session."""


def object_key(session_id: str) -> str:
    """
    S3/local key for a session's category CSV.

    Example: categories/<uuid>/categories.csv
    """
    return f"{CATEGORY_KEY_PREFIX}/{session_id}/{CATEGORY_KEY_FILENAME}"


class LocalCategoryStore(CategoryStore):
    """Session-scoped category files under categories/<session_id>/categories.csv."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or os.getcwd()

    def _path(self, session_id: str) -> str:
        return os.path.join(self.base_dir, object_key(session_id))

    def save(self, df: pd.DataFrame, session_id: str) -> None:
        path = self._path(session_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)

    def load(self, session_id: str) -> pd.DataFrame:
        path = self._path(session_id)
        if not os.path.isfile(path):
            raise CategoryNotFoundError(
                f"Categories not found for session {session_id}"
            )
        return pd.read_csv(path, dtype={"Question Id": str})


class S3CategoryStore(CategoryStore):
    """Session-scoped category objects in S3."""

    def __init__(
        self,
        bucket: str,
        region: str | None = None,
        client=None,
    ):
        self.bucket = bucket
        self._client = client or boto3.client("s3", region_name=region)

    def save(self, df: pd.DataFrame, session_id: str) -> None:
        key = object_key(session_id)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        try:
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=buffer.getvalue().encode("utf-8"),
                ContentType="text/csv",
            )
        except ClientError as e:
            _raise_from_client_error(e, session_id)
        except BotoCoreError as e:
            raise CategoryStoreError(f"S3 unavailable: {e}") from e

    def load(self, session_id: str) -> pd.DataFrame:
        key = object_key(session_id)
        try:
            response = self._client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"].read()
            return pd.read_csv(io.BytesIO(body), dtype={"Question Id": str})
        except ClientError as e:
            _raise_from_client_error(e, session_id)
        except BotoCoreError as e:
            raise CategoryStoreError(f"S3 unavailable: {e}") from e


def _raise_from_client_error(error: ClientError, session_id: str) -> None:
    code = error.response.get("Error", {}).get("Code", "")
    if code in ("NoSuchKey", "404", "NotFound"):
        raise CategoryNotFoundError(
            f"Categories not found for session {session_id}"
        ) from error
    if code in ("AccessDenied", "403", "Forbidden"):
        raise CategoryStorePermissionError(
            f"Permission denied reading categories for session {session_id}"
        ) from error
    raise CategoryStoreError(f"S3 error ({code}): {error}") from error


def get_category_store() -> CategoryStore:
    """
    Return the configured category store implementation.

    CATEGORY_STORE_TYPE:
      local (default) — LocalCategoryStore
      s3              — S3CategoryStore (requires CATEGORY_BUCKET_NAME)
    """
    store_type = os.getenv("CATEGORY_STORE_TYPE", "local").lower()
    if store_type == "s3":
        bucket = os.getenv("CATEGORY_BUCKET_NAME")
        if not bucket:
            raise CategoryStoreError(
                "CATEGORY_BUCKET_NAME is required when CATEGORY_STORE_TYPE=s3"
            )
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        return S3CategoryStore(bucket=bucket, region=region)
    return LocalCategoryStore()
