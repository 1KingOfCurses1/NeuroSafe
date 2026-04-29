from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "neurosafe-backend",
        "environment": settings.APP_ENV,
        "model_provider": settings.MODEL_PROVIDER
    }
