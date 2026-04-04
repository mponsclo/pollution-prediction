"""Health check endpoint."""

from fastapi import APIRouter, Request

from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request):
    models = getattr(request.app.state, "models", {})
    return HealthResponse(
        status="healthy",
        models_loaded=len(models),
    )
