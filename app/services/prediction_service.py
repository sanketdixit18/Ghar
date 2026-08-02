"""
PredictionService
------------------
Reuses the existing trained pipelines exactly as-is:
    prediction = pipeline.predict(input_df)
    predicted_price = np.expm1(prediction)[0]

No retraining, no changes to preprocessing or the model. This mirrors
utils/prediction.py's make_prediction() from the original Streamlit app.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from app.config import DEFAULT_ERROR_MARGIN_PCT
from app.services.loader import city_manager

logger = logging.getLogger("real_estate.prediction")


class PredictionService:

    def get_form_schema(self, city: str) -> list[dict[str, Any]]:
        """Build the dynamic prediction form for a city from its config.json
        + the live values found in df.pkl (mirrors the original
        `sorted(df[feature].unique())` selectbox population)."""
        cfg = city_manager.get_config(city)
        df, _ = city_manager.load_prediction_assets(city)

        fields = []
        for feature, details in cfg.get("prediction_inputs", {}).items():
            field: dict[str, Any] = {
                "name": feature,
                "label": details.get("label", feature.replace("_", " ").title()),
                "type": details["type"],
            }
            if details["type"] == "select":
                if feature in df.columns:
                    values = df[feature].dropna().unique().tolist()
                    try:
                        values = sorted(values)
                    except TypeError:
                        values = sorted(values, key=str)
                    field["options"] = values
                else:
                    field["options"] = []
            elif details["type"] == "number":
                field["min"] = details.get("min", 100)
                field["step"] = details.get("step", 50)
            fields.append(field)
        return fields

    def predict(self, city: str, features: dict[str, Any]) -> dict[str, Any]:
        cfg = city_manager.get_config(city)
        df, pipeline = city_manager.load_prediction_assets(city)

        if pipeline is None:
            raise RuntimeError(f"No trained model is available for {city} yet.")

        expected_columns = list(cfg.get("prediction_inputs", {}).keys())
        missing = [c for c in expected_columns if c not in features]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        row = [features[col] for col in expected_columns]
        input_df = pd.DataFrame([row], columns=expected_columns)

        # Cast numeric fields declared as "number" in config to float, so a
        # value coming in as a string from an HTML form still works.
        for col, details in cfg.get("prediction_inputs", {}).items():
            if details["type"] == "number":
                input_df[col] = pd.to_numeric(input_df[col], errors="coerce")

        raw_prediction = pipeline.predict(input_df)
        predicted_price = float(np.expm1(raw_prediction)[0])

        error_margin = predicted_price * DEFAULT_ERROR_MARGIN_PCT
        lower_price = max(predicted_price - error_margin, 0.0)
        upper_price = predicted_price + error_margin

        return {
            "predicted_price": round(predicted_price, 2),
            "lower_estimate": round(lower_price, 2),
            "upper_estimate": round(upper_price, 2),
            "currency": cfg.get("currency", "\u20b9"),
            "unit": cfg.get("unit", "Cr"),
            "input_summary": {col: features[col] for col in expected_columns},
        }


prediction_service = PredictionService()
