from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "env": settings.app_env,
        "model": settings.llm_model_balanced,
    }
