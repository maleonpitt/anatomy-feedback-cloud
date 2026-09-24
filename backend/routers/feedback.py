"""Send-feedback route."""

from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from services.email_delivery import deliver_student_feedback

logger = logging.getLogger(__name__)
router = APIRouter(tags=["feedback"])


@router.post("/send-feedback")
async def send_feedback(request: Request):
    try:
        if "user_email" not in request.session:
            return JSONResponse({"error": "Not authenticated"}, status_code=401)

        try:
            data = await request.json()
        except Exception:
            data = None

        if not data or "feedback" not in data:
            return JSONResponse({"error": "No feedback data provided"}, status_code=400)

        feedback_data = data["feedback"]
        test_name = (data.get("test_name") or "").strip()
        instructor_name = (data.get("instructor_name") or "").strip()
        access_token = request.session.get("oauth_token", {}).get("access_token")

        logger.info(f"Feedback data keys received: {list(feedback_data.keys())}")

        for email, feedback in feedback_data.items():
            if isinstance(feedback, str):
                try:
                    feedback = json.loads(feedback)
                except Exception:
                    logger.warning(f"Skipping {email}: feedback not valid JSON string.")
                    continue

            if not isinstance(feedback, dict):
                logger.warning(
                    f"Skipping {email}: invalid feedback format ({type(feedback).__name__})"
                )
                continue

            try:
                deliver_student_feedback(
                    email,
                    feedback,
                    test_name,
                    instructor_name,
                    flask_env=os.getenv("FLASK_ENV"),
                    access_token=access_token,
                )
            except Exception as inner_e:
                logger.error(f"Failed to send feedback for {email}: {str(inner_e)}")

        return JSONResponse(
            {"message": "Feedback sent successfully"}, status_code=200
        )
    except Exception as e:
        logger.error(f"Send feedback error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)
