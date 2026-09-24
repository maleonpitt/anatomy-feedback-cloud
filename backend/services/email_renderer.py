"""Structured HTML email rendering (production email body shape)."""

from __future__ import annotations

from typing import Any


def build_email_subject(test_name: str | None) -> str:
    if test_name:
        return f"Feedback for {test_name}"
    return "Your Feedback from the Last Assessment"


def render_structured_email_html(
    feedback: dict[str, Any], instructor_name: str | None = None
) -> str:
    """
    Build the production HTML body that mirrors the frontend feedback card.

    Does not send email and does not call OpenAI.
    """
    predicted_grade = feedback.get("predicted_grade", "N/A")
    score = feedback.get("score", "N/A")
    categories = feedback.get("summary", {}) or {}
    modules = feedback.get("categories", []) or []
    most_work = feedback.get("most_work_category", "N/A")

    grade_section = f"""
    <div style="border: 2px solid #1a73e8; background-color:#f7faff; border-radius:6px; padding:10px; margin-top:8px; width:fit-content;">
        <h3 style="color:#1a73e8; margin:0;">Predicted Course Grade: {predicted_grade}</h3>
    </div>
    """

    bullet_points = "".join(
        f"<li>{cat}: {count} wrong</li>" for cat, count in categories.items()
    )
    module_points = "".join(
        f"<li>{m.get('category', 'Unknown')}: {m.get('module', 'Unknown')}</li>"
        for m in modules
    )

    formatted_summary = f"""
    <div style="font-family:Arial, sans-serif; font-size:14px; color:#202124; line-height:1.6;">
        <p><strong>Exam Score:</strong> {score}</p>

        <p><strong>Summary of Incorrect Answers:</strong></p>
        <ul style="margin-top:-8px;">{bullet_points or '<li>None</li>'}</ul>

        <p><strong>Modules to Focus On:</strong></p>
        <ul style="margin-top:-8px;">{module_points or '<li>None</li>'}</ul>

        <p><strong>Needs Most Work:</strong> {most_work}</p>
    </div>
    """

    return f"""
    <html>
    <body style="font-family:Arial, sans-serif; background-color:#ffffff; color:#202124; margin:0; padding:20px;">
        <div style="max-width:600px; margin:auto; border:1px solid #e0e0e0; border-radius:8px; padding:20px; background-color:#fafafa;">
            <p style="font-size:16px; margin-bottom:16px;">Dear Student,</p>
            <p style="font-size:14px; line-height:1.6;">I hope this message finds you well.</p>

            {grade_section}

            <div style="margin-top:15px;">
                {formatted_summary}
            </div>

            <p style="font-size:14px; line-height:1.6; margin-top:20px;">
                Keep up your hard work — continued focus on these areas will help you excel further.
            </p>

            <p style="font-style: italic; margin-top:24px;">Best regards,<br>{instructor_name}</p>
        </div>
    </body>
    </html>
    """
