"""Excel parsing and feedback dictionary construction."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, BinaryIO

import pandas as pd

CATEGORY_USECOLS = ["Question Id", "Category", "Module", "Question Title"]
STUDENT_META_COLUMNS = ["Participant Number", "Email", "score", "Predicted Grade"]


def parse_categories_excel(file_obj: BinaryIO | Any) -> pd.DataFrame:
    """
    Parse the categories workbook.

    Raises whatever pandas raises on missing columns / bad files
    (callers historically map that to HTTP 500).
    """
    df = pd.read_excel(file_obj, usecols=CATEGORY_USECOLS)
    df["Question Id"] = df["Question Id"].astype(str)
    return df


def parse_student_excel(file_obj: BinaryIO | Any) -> pd.DataFrame:
    return pd.read_excel(file_obj)


def build_feedback_dict(
    student_df: pd.DataFrame, categories_df: pd.DataFrame
) -> dict[str, dict[str, Any]]:
    """
    Build per-email feedback from student answers + category map.

    Current rules:
    - answer == 0 means incorrect
    - unknown question IDs are ignored
    - duplicate emails: last row wins
    """
    feedback_dict: dict[str, dict[str, Any]] = {}
    known_ids = set(categories_df["Question Id"].astype(str).values)

    question_columns = [
        col for col in student_df.columns if col not in STUDENT_META_COLUMNS
    ]

    for _, row in student_df.iterrows():
        email = row["Email"]
        category_count: defaultdict[str, int] = defaultdict(int)
        feedback: list[dict[str, str]] = []

        for qid in question_columns:
            qid_str = str(qid)
            if qid_str in known_ids and row[qid] == 0:
                category_info = categories_df[
                    categories_df["Question Id"] == qid_str
                ].iloc[0]
                feedback.append(
                    {
                        "category": category_info["Category"],
                        "module": category_info["Module"],
                    }
                )
                category_count[category_info["Category"]] += 1

        feedback_dict[email] = {
            "score": row.get("score", "N/A"),
            "predicted_grade": row.get("Predicted Grade", "N/A"),
            "categories": feedback,
            "summary": dict(category_count),
            "most_work_category": max(
                category_count, key=category_count.get, default=None
            ),
        }

    return feedback_dict


def build_feedback_from_upload(
    file_obj: BinaryIO | Any, categories_df: pd.DataFrame
) -> dict[str, dict[str, Any]]:
    student_df = parse_student_excel(file_obj)
    return build_feedback_dict(student_df, categories_df)
