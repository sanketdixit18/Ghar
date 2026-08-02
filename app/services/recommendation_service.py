"""
RecommendationService
-----------------------
Same cosine/hybrid-similarity lookup as utils/recommendation.py:
    distances = sorted(enumerate(similarity[index]), reverse=True, key=lambda x: x[1])[1:top_n+1]
The [1:] skips the property itself (always similarity 1.0 / index 0 match).
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.loader import city_manager

logger = logging.getLogger("real_estate.recommendation")


class RecommendationService:

    def is_available(self, city: str) -> bool:
        recommend_df, similarity = city_manager.load_recommendation_assets(city)
        return recommend_df is not None and similarity is not None

    def list_properties(self, city: str) -> list[str]:
        recommend_df, _ = city_manager.load_recommendation_assets(city)
        if recommend_df is None:
            return []
        return sorted(recommend_df["property_name"].unique().tolist())

    def recommend(self, city: str, property_name: str, top_n: int = 5) -> dict[str, Any]:
        recommend_df, similarity = city_manager.load_recommendation_assets(city)
        if recommend_df is None or similarity is None:
            raise RuntimeError(f"Recommendations are not available for {city}.")

        matches = recommend_df[recommend_df["property_name"] == property_name]
        if matches.empty:
            raise ValueError(f"Property '{property_name}' not found.")
        index = matches.index[0]

        distances = list(enumerate(similarity[index]))
        distances = sorted(distances, reverse=True, key=lambda x: x[1])[1: top_n + 1]

        recommendations = []
        for i, score in distances:
            prop = recommend_df.iloc[i]

            facilities = prop.get("facilities") or []
            nearby = prop.get("nearby") or []
            price_details = prop.get("price_details") or {}

            recommendations.append({
                "property_name": prop["property_name"],
                "match_score": round(float(score) * 100, 2),
                "avg_price": round(float(prop["avg_price"]), 2) if pd_notna(prop.get("avg_price")) else None,
                "amenities": list(facilities)[:5],
                "nearby": list(nearby)[:5],
                "configurations": list(price_details.keys()),
                "link": prop.get("link"),
            })

        return {
            "query_property": property_name,
            "recommendations": recommendations,
        }


def pd_notna(value) -> bool:
    try:
        import pandas as pd
        return pd.notna(value)
    except Exception:  # noqa: BLE001
        return value is not None


recommendation_service = RecommendationService()
