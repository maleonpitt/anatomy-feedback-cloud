"""Characterize Excel upload endpoints and feedback-building behavior."""

from pathlib import Path

from tests.conftest import (
    build_categories_workbook,
    build_student_workbook,
    upload_categories,
    upload_mockdata,
)


def test_upload_categories_valid_writes_session_scoped_categories(
    client, categories_xlsx_bytes, tmp_path
):
    response = upload_categories(client, categories_xlsx_bytes)
    assert response.status_code == 200
    assert response.json() == {"message": "Categories uploaded successfully"}
    category_root = tmp_path / "categories"
    assert category_root.is_dir()
    session_dirs = list(category_root.iterdir())
    assert len(session_dirs) == 1
    assert (session_dirs[0] / "categories.csv").is_file()


def test_upload_categories_missing_file_returns_400(client):
    response = client.post("/upload-categories")
    assert response.status_code == 400
    assert response.json() == {"error": "No file provided"}


def test_upload_categories_missing_required_columns_returns_500(client):
    """Current behavior: pandas usecols failure surfaces as HTTP 500 with error body."""
    bad = build_categories_workbook(
        headers=["Wrong", "Headers", "Here", "Only"],
        rows=[("a", "b", "c", "d")],
    )
    response = upload_categories(client, bad)
    assert response.status_code == 500
    body = response.json()
    assert "error" in body
    assert body["error"]


def test_upload_mockdata_missing_categories_file_returns_500(client, student_xlsx_bytes):
    """Current behavior: no prior category upload → HTTP 500 with error body."""
    assert not Path("categories").exists()
    response = upload_mockdata(client, student_xlsx_bytes)
    assert response.status_code == 500
    body = response.json()
    assert "error" in body
    assert body["error"]


def test_upload_mockdata_missing_file_returns_400(client, categories_xlsx_bytes, tmp_path):
    upload_categories(client, categories_xlsx_bytes)
    assert (tmp_path / "categories").is_dir()

    response = client.post("/upload-mockdata")
    assert response.status_code == 400
    assert response.json() == {"error": "No file provided"}


def test_upload_mockdata_valid_returns_expected_feedback_structure(
    client, categories_xlsx_bytes, student_xlsx_bytes
):
    upload_categories(client, categories_xlsx_bytes)
    response = upload_mockdata(client, student_xlsx_bytes)
    assert response.status_code == 200

    data = response.json()
    assert "student1@example.edu" in data
    student = data["student1@example.edu"]
    assert set(student.keys()) >= {
        "score",
        "predicted_grade",
        "categories",
        "summary",
        "most_work_category",
    }
    assert student["score"] == 80
    assert student["predicted_grade"] == "B"
    assert student["summary"] == {"Bones": 1}
    assert student["most_work_category"] == "Bones"
    assert student["categories"] == [
        {"category": "Bones", "module": "Module A"},
    ]


def test_zero_means_incorrect_nonzero_not_counted(client, categories_xlsx_bytes):
    """Q1=0 → incorrect; Q2=1 → not treated as incorrect (current rule)."""
    upload_categories(client, categories_xlsx_bytes)
    students = build_student_workbook(
        rows=[
            (1, "student1@example.edu", 90, "A", 0, 1, 0),
        ]
    )
    data = upload_mockdata(client, students).json()
    student = data["student1@example.edu"]
    cats = {(c["category"], c["module"]) for c in student["categories"]}
    assert ("Bones", "Module A") in cats
    assert ("Muscles", "Module B") not in cats
    assert student["summary"].get("Muscles") is None


def test_unknown_question_ids_are_ignored(client, categories_xlsx_bytes):
    """Q999 is not in categories; even with answer 0 it must not appear."""
    upload_categories(client, categories_xlsx_bytes)
    students = build_student_workbook(
        rows=[
            (1, "student1@example.edu", 70, "C", 1, 1, 0),
        ]
    )
    data = upload_mockdata(client, students).json()
    student = data["student1@example.edu"]
    assert student["categories"] == []
    assert student["summary"] == {}
    assert student["most_work_category"] is None


def test_uploads_do_not_require_authentication(
    client, categories_xlsx_bytes, student_xlsx_bytes
):
    """
    Characterization of current (insecure) behavior:
    upload endpoints succeed without a session.
    """
    cat = upload_categories(client, categories_xlsx_bytes)
    mock = upload_mockdata(client, student_xlsx_bytes)
    assert cat.status_code == 200
    assert mock.status_code == 200
