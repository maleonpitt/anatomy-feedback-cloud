"""Excel upload routes."""

from __future__ import annotations

import io
import logging
from typing import Optional

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from services.category_session import (
    get_category_session_id,
    get_or_create_category_session_id,
)
from services.category_store import CategoryNotFoundError, get_category_store
from services.excel_service import build_feedback_from_upload, parse_categories_excel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["uploads"])


def _missing_file_response() -> JSONResponse:
    return JSONResponse({"error": "No file provided"}, status_code=400)


@router.post("/upload-categories")
async def upload_categories(
    request: Request, file: Optional[UploadFile] = File(None)
):
    try:
        if file is None:
            return _missing_file_response()

        contents = await file.read()
        if not contents and not file.filename:
            return _missing_file_response()

        session_id = get_or_create_category_session_id(request.session)
        df = parse_categories_excel(io.BytesIO(contents))
        get_category_store().save(df, session_id)
        return JSONResponse(
            {"message": "Categories uploaded successfully"}, status_code=200
        )
    except Exception as e:
        logger.error(f"Upload categories error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/upload-mockdata")
async def upload_mockdata(request: Request, file: Optional[UploadFile] = File(None)):
    try:
        session_id = get_category_session_id(request.session)
        if not session_id:
            raise CategoryNotFoundError("No categories uploaded for this session")

        categories_df = get_category_store().load(session_id)
        if file is None:
            return _missing_file_response()

        contents = await file.read()
        if not contents and not file.filename:
            return _missing_file_response()

        feedback_dict = build_feedback_from_upload(
            io.BytesIO(contents), categories_df
        )
        return JSONResponse(feedback_dict, status_code=200)
    except Exception as e:
        logger.error(f"Upload mockdata error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)
