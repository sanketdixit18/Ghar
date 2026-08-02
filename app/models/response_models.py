"""Response models (Pydantic v2)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class CityConfig(BaseModel):
    """Public-facing summary of a discovered city."""

    model_config = ConfigDict(extra="allow")

    slug: str
    city: str
    state: str | None = None
    currency: str = "\u20b9"
    unit: str = "Cr"
    theme: str = "blue"
    emoji: str = "\ud83c\udfd9\ufe0f"
    tag: str | None = None
    status: str = "active"
    description: str | None = None
    features: dict[str, bool] = {}


class PredictionInputField(BaseModel):
    name: str
    label: str
    type: str
    options: list[Any] | None = None
    min: float | None = None
    step: float | None = None


class PredictionFormSchema(BaseModel):
    city: str
    fields: list[PredictionInputField]


class PredictionResponse(BaseModel):
    predicted_price: float
    lower_estimate: float
    upper_estimate: float
    currency: str = "\u20b9"
    unit: str = "Cr"
    input_summary: dict[str, Any]


class RecommendedProperty(BaseModel):
    property_name: str
    match_score: float
    avg_price: float | None = None
    amenities: list[str] = []
    nearby: list[str] = []
    configurations: list[str] = []
    link: str | None = None


class RecommendationResponse(BaseModel):
    query_property: str
    recommendations: list[RecommendedProperty]


class AnalyticsResponse(BaseModel):
    city: str
    kpis: dict[str, Any]
    charts: dict[str, Any]
    available: dict[str, bool]


class HealthResponse(BaseModel):
    status: str
    version: str
    cities_loaded: list[str]
