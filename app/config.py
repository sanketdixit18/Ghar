"""
Application-wide configuration.

Nothing city-specific lives here — that all comes from each city's
models/<city>/config.json, discovered dynamically by CityManager.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
LOGS_DIR = Path(os.getenv("LOGS_DIR", BASE_DIR / "logs"))
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------
APP_NAME = "Real Estate Price Prediction System"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Sanket Dixit"
APP_DESCRIPTION = (
    "An end-to-end Machine Learning application that estimates residential "
    "property prices using models trained on real transaction and listing "
    "data — covering data cleaning, feature engineering, model training, "
    "and an interactive prediction interface."
)
LINKEDIN_URL = "https://linkedin.com/in/sanket-dixit-85983a243"
GITHUB_URL = "https://github.com/sanketdixit18/Real-estate-app"

# ---------------------------------------------------------------------------
# Runtime settings
# ---------------------------------------------------------------------------
ENV = os.getenv("ENVIRONMENT", "production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Approximate prediction error margin (fallback when a model has no
# published RMSE) — kept identical to the original Streamlit behaviour.
DEFAULT_ERROR_MARGIN_PCT = 0.05

# Snapshot metrics shown on the home page (cosmetic, same as the original app.py)
PROJECT_METRICS = [
    {"label": "R\u00b2 Score", "value": "97.8%"},
    {"label": "MAE", "value": "\u20b918 Lakh"},
    {"label": "Properties Analyzed", "value": "75k+"},
    {"label": "Features Engineered", "value": "20+"},
]
