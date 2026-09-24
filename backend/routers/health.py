"""Health check route."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy"}, status_code=200)
