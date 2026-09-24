"""OpenAI narrative summary used by the local email-preview path only."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

import openai

logger = logging.getLogger(__name__)


def generate_feedback_summary(feedback: Any) -> str:
    """
    Call OpenAI (legacy 0.28 ChatCompletion API) for a narrative summary.

    Used only when FLASK_ENV=local for HTML preview files.
    """
    try:
        if isinstance(feedback, str):
            try:
                feedback = json.loads(feedback)
            except Exception:
                logger.warning("Feedback was a string but not valid JSON.")
                return "Feedback format invalid for this student."

        if not isinstance(feedback, dict):
            logger.warning(
                f"Skipping invalid feedback entry (expected dict, got {type(feedback).__name__})"
            )
            return "Feedback data was not formatted correctly for this student."

        categories = feedback.get("summary", {}) or {}
        modules: defaultdict[str, set] = defaultdict(set)

        for item in feedback.get("categories", []):
            if isinstance(item, dict):
                modules[item.get("category", "Unknown")].add(
                    item.get("module", "Unknown")
                )

        bullet_points = "\n".join(
            [f"- {cat}: {count} incorrect answers" for cat, count in categories.items()]
        )
        modules_to_review = "\n".join(
            [f"- {cat}: {', '.join(sorted(mods))}" for cat, mods in modules.items()]
        )
        predicted_grade = feedback.get("predicted_grade", "N/A")

        prompt = f"""
You are an instructor writing a feedback email to a student after a test. Use a warm, encouraging tone.

Here is the student's performance data:

Score: {feedback.get('score', 'N/A')}
Predicted Grade: {predicted_grade}

Incorrect Answers by Category:
{bullet_points}

Modules to Focus On:
{modules_to_review}

Category that needs the most work:
{feedback.get('most_work_category', 'None')}

Write a brief summary of 2–3 paragraphs that thanks the student, summarizes their performance, mentions their predicted grade, and encourages them to review the listed areas.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )

        return response.choices[0].message["content"].strip()

    except Exception as e:
        logger.error(f"OpenAI feedback generation failed: {str(e)}")
        return (
            "We encountered an issue generating your feedback. "
            "Please consult your instructor."
        )
