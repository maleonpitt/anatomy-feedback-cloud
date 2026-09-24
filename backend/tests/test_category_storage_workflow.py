"""HTTP tests for session-scoped category storage workflow."""

import io
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from tests.conftest import (
    build_categories_workbook,
    build_student_workbook,
    upload_categories,
    upload_mockdata,
)


def test_category_upload_then_mockdata_uses_same_session(client, tmp_path):
    """Same TestClient session ties both uploads to one category store key."""
    cat = upload_categories(client, build_categories_workbook())
    assert cat.status_code == 200

    category_dirs = list((tmp_path / "categories").iterdir())
    assert len(category_dirs) == 1
    assert (category_dirs[0] / "categories.csv").is_file()

    mock = upload_mockdata(client, build_student_workbook())
    assert mock.status_code == 200
    assert "student1@example.edu" in mock.json()


def test_mockdata_without_prior_category_upload_returns_500(client, student_xlsx_bytes):
    response = upload_mockdata(client, student_xlsx_bytes)
    assert response.status_code == 500
    assert "error" in response.json()


def test_s3_workflow_across_distinct_store_instances(client, monkeypatch):
    """
    Simulate instance A saving and instance B loading via separate S3CategoryStore
    objects backed by the same in-memory bucket (no shared local filesystem).
    """
    monkeypatch.setenv("CATEGORY_STORE_TYPE", "s3")
    monkeypatch.setenv("CATEGORY_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    memory: dict[str, bytes] = {}

    def put_object(**kwargs):
        memory[kwargs["Key"]] = kwargs["Body"]

    def get_object(**kwargs):
        key = kwargs["Key"]
        if key not in memory:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "test"}},
                "GetObject",
            )
        return {"Body": io.BytesIO(memory[key])}

    mock_client = MagicMock()
    mock_client.put_object.side_effect = put_object
    mock_client.get_object.side_effect = get_object

    with patch("services.category_store.boto3.client", return_value=mock_client):
        cat = upload_categories(client, build_categories_workbook())
        assert cat.status_code == 200
        assert len(memory) == 1

        mock = upload_mockdata(client, build_student_workbook())
        assert mock.status_code == 200
        assert "student1@example.edu" in mock.json()
