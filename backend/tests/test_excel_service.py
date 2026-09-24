"""Unit tests for extracted excel / category-store logic."""

import io

import pandas as pd
import pytest

from services.category_store import (
    CategoryNotFoundError,
    LocalCategoryStore,
    object_key,
)
from services.excel_service import (
    build_feedback_dict,
    parse_categories_excel,
)
from tests.conftest import build_categories_workbook

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


def test_parse_categories_excel_normalizes_question_ids():
    raw = build_categories_workbook(
        rows=[(101, "Bones", "Module A", "Title")],
    )
    df = parse_categories_excel(io.BytesIO(raw))
    assert list(df.columns) == [
        "Question Id",
        "Category",
        "Module",
        "Question Title",
    ]
    assert df.iloc[0]["Question Id"] == "101"


def test_parse_categories_excel_missing_columns_raises():
    raw = build_categories_workbook(
        headers=["Wrong", "Headers", "Here", "Only"],
        rows=[("a", "b", "c", "d")],
    )
    with pytest.raises(Exception):
        parse_categories_excel(io.BytesIO(raw))


def test_build_feedback_zero_incorrect_nonzero_ignored():
    categories = pd.DataFrame(
        [
            {
                "Question Id": "Q1",
                "Category": "Bones",
                "Module": "Module A",
                "Question Title": "t1",
            },
            {
                "Question Id": "Q2",
                "Category": "Muscles",
                "Module": "Module B",
                "Question Title": "t2",
            },
        ]
    )
    students = pd.DataFrame(
        [
            {
                "Participant Number": 1,
                "Email": "s@ex.edu",
                "score": 80,
                "Predicted Grade": "B",
                "Q1": 0,
                "Q2": 1,
                "Q999": 0,
            }
        ]
    )
    result = build_feedback_dict(students, categories)
    entry = result["s@ex.edu"]
    assert entry["summary"] == {"Bones": 1}
    assert entry["categories"] == [{"category": "Bones", "module": "Module A"}]
    assert entry["most_work_category"] == "Bones"
    assert entry["score"] == 80
    assert entry["predicted_grade"] == "B"


def test_build_feedback_unknown_question_ids_ignored():
    categories = pd.DataFrame(
        [
            {
                "Question Id": "Q1",
                "Category": "Bones",
                "Module": "A",
                "Question Title": "t",
            }
        ]
    )
    students = pd.DataFrame(
        [
            {
                "Participant Number": 1,
                "Email": "s@ex.edu",
                "score": 70,
                "Predicted Grade": "C",
                "Q1": 1,
                "Q999": 0,
            }
        ]
    )
    entry = build_feedback_dict(students, categories)["s@ex.edu"]
    assert entry["categories"] == []
    assert entry["summary"] == {}
    assert entry["most_work_category"] is None


def test_local_category_store_roundtrip(tmp_path):
    store = LocalCategoryStore(base_dir=str(tmp_path))
    session_id = "session-abc"
    store.save(SAMPLE_DF, session_id)
    loaded = store.load(session_id)
    assert loaded.iloc[0]["Question Id"] == "Q1"
    assert loaded.iloc[0]["Category"] == "Bones"
    assert (tmp_path / object_key(session_id)).is_file()


def test_local_category_store_missing_file_raises(tmp_path):
    store = LocalCategoryStore(base_dir=str(tmp_path))
    with pytest.raises(CategoryNotFoundError):
        store.load("missing-session")


def test_local_category_store_sessions_are_isolated(tmp_path):
    store = LocalCategoryStore(base_dir=str(tmp_path))
    df_a = SAMPLE_DF.copy()
    df_b = SAMPLE_DF.copy()
    df_b.iloc[0, df_b.columns.get_loc("Category")] = "Muscles"

    store.save(df_a, "session-a")
    store.save(df_b, "session-b")

    assert store.load("session-a").iloc[0]["Category"] == "Bones"
    assert store.load("session-b").iloc[0]["Category"] == "Muscles"
