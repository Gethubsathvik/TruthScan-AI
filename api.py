"""
FastAPI REST service — a thin HTTP wrapper around PredictionService.

Run with:  uvicorn api:app --reload
Docs at:   http://localhost:8000/docs
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.models.predict import EmptyInputError, ModelNotFoundError, PredictionService
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Fake News Detection API",
    description=(
        "Classical machine-learning REAL/FAKE text classification. "
        "This is a pattern-based classifier, not a fact-checking service — "
        "see the `disclaimer` field on every /predict response."
    ),
    version="1.0.0",
)


class PredictRequest(BaseModel):
    title: str = Field(default="", description="News headline")
    text: str = Field(default="", description="Full article body")


class FeatureContributionOut(BaseModel):
    feature: str
    weight: float
    direction: str


class PredictResponse(BaseModel):
    prediction: str
    confidence: float | None
    confidence_level: str
    is_calibrated_probability: bool
    model: str
    top_features: list[FeatureContributionOut]
    disclaimer: str


class HealthResponse(BaseModel):
    status: str


@lru_cache(maxsize=1)
def get_service() -> PredictionService:
    return PredictionService(config=config)


@app.exception_handler(ModelNotFoundError)
async def handle_model_not_found(request, exc: ModelNotFoundError) -> JSONResponse:
    logger.error("Model not available: %s", exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Lightweight liveness check — does not require a trained model."""
    return HealthResponse(status="healthy")


@app.get("/model/info")
def model_info(service: PredictionService = Depends(get_service)) -> dict:
    """Returns metadata.json for the currently loaded model (name, metrics,
    dataset info, feature config)."""
    return service.metadata


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, service: PredictionService = Depends(get_service)) -> PredictResponse:
    try:
        result = service.predict(title=payload.title, text=payload.text)
    except EmptyInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PredictResponse(**result.to_dict())
