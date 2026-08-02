"""Request validation models (Pydantic v2)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PredictionRequest(BaseModel):
    """
    Generic prediction request.

    The set of valid keys is city-specific (see models/<city>/config.json ->
    prediction_inputs), so we accept an open dict of feature -> value and
    validate it against that city's schema inside PredictionService. This is
    what lets a new city be added without touching this model.
    """

    model_config = ConfigDict(extra="allow")

    city: str = Field(..., min_length=1, description="City slug, e.g. 'gurgaon'")
    features: dict[str, Any] = Field(
        ..., description="Feature name -> user-selected value, per the city's prediction_inputs"
    )

    @field_validator("city")
    @classmethod
    def normalize_city(cls, v: str) -> str:
        return v.strip().lower()


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str = Field(..., min_length=1)
    property_name: str = Field(..., min_length=1)
    top_n: int = Field(5, ge=1, le=20)

    @field_validator("city")
    @classmethod
    def normalize_city(cls, v: str) -> str:
        return v.strip().lower()


class AnalyticsFilterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str
    sector: str | None = "All"
    price_min: float | None = None
    price_max: float | None = None
    property_type: str | None = "All"
    bedrooms: str | None = "All"

    @field_validator("city")
    @classmethod
    def normalize_city(cls, v: str) -> str:
        return v.strip().lower()


class MarketFilterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str
    locality: str | None = "All"
    builder: str | None = "All"
    property_type: str | None = "All"
    price_segment: str | None = "All"

    @field_validator("city")
    @classmethod
    def normalize_city(cls, v: str) -> str:
        return v.strip().lower()
