"""
LoaderService / CityManager
----------------------------
The single source of truth for "which cities exist and what data/models do
they have". Everything else in the app (routers, other services) goes
through this module instead of touching the filesystem directly.

Adding a new city requires ZERO code changes here: drop a folder under
/models/<slug>/ with a config.json + df.pkl (+ optional pipeline.pkl,
recommend_df.pkl, hybrid_similarity.pkl), and matching CSVs under
/data/<slug>/. On next startup (or the next call, since discovery is
re-run if a new folder appears) it is picked up automatically.
"""
from __future__ import annotations

import json
import logging
import pickle
import threading
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import DATA_DIR, MODELS_DIR

logger = logging.getLogger("real_estate.loader")


@dataclass
class CityAssets:
    """Everything loaded/cached in memory for a single city."""

    slug: str
    config: dict[str, Any]

    df: pd.DataFrame | None = None
    pipeline: Any = None
    analytics_df: pd.DataFrame | None = None
    wordcloud_df: pd.DataFrame | None = None
    market_df: pd.DataFrame | None = None
    recommend_df: pd.DataFrame | None = None
    similarity: Any = None

    _loaded_flags: set[str] = field(default_factory=set)


class CityManager:
    """
    Thread-safe, lazy-loading, caching manager for all discovered cities.

    - discover_cities() scans MODELS_DIR for config.json files (cheap, no
      pickle/CSV loading) so route handlers like GET /cities are fast.
    - get_assets(slug) lazily loads and permanently caches the heavier
      artifacts (df.pkl, pipeline.pkl, csvs) the first time they're needed.
      Once loaded, a city is never reloaded/re-read from disk.
    """

    def __init__(self, models_dir: Path = MODELS_DIR, data_dir: Path = DATA_DIR):
        self.models_dir = models_dir
        self.data_dir = data_dir
        self._configs: dict[str, dict[str, Any]] = {}
        self._assets: dict[str, CityAssets] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    def discover_cities(self, force: bool = False) -> dict[str, dict[str, Any]]:
        """Scan the models directory for city folders containing config.json."""
        with self._lock:
            if self._configs and not force:
                return self._configs

            configs: dict[str, dict[str, Any]] = {}
            if not self.models_dir.exists():
                logger.warning("Models directory %s does not exist", self.models_dir)
                self._configs = configs
                return configs

            for entry in sorted(self.models_dir.iterdir()):
                if not entry.is_dir():
                    continue
                config_path = entry / "config.json"
                if not config_path.exists():
                    logger.debug("Skipping %s: no config.json", entry.name)
                    continue
                try:
                    with open(config_path, encoding="utf-8") as f:
                        cfg = json.load(f)
                except (json.JSONDecodeError, OSError) as exc:
                    logger.error("Failed to read config for %s: %s", entry.name, exc)
                    continue

                cfg.setdefault("city", entry.name.title())
                cfg.setdefault("status", "active")
                cfg.setdefault("features", {})
                configs[entry.name.lower()] = cfg
                logger.info("Discovered city: %s (%s)", entry.name, cfg.get("city"))

            self._configs = configs
            return configs

    def list_cities(self, active_only: bool = True) -> list[dict[str, Any]]:
        configs = self.discover_cities()
        out = []
        for slug, cfg in configs.items():
            if active_only and cfg.get("status") != "active":
                continue
            out.append({"slug": slug, **cfg})
        return out

    def get_config(self, slug: str) -> dict[str, Any]:
        slug = slug.lower()
        configs = self.discover_cities()
        if slug not in configs:
            # one retry with a forced re-scan, in case a city was added
            # after the process started
            configs = self.discover_cities(force=True)
        if slug not in configs:
            raise KeyError(f"Unknown city: {slug}")
        return configs[slug]

    def city_exists(self, slug: str) -> bool:
        try:
            self.get_config(slug)
            return True
        except KeyError:
            return False

    # ------------------------------------------------------------------
    # Lazy asset loading (never reloads once cached)
    # ------------------------------------------------------------------
    def get_assets(self, slug: str) -> CityAssets:
        slug = slug.lower()
        with self._lock:
            if slug in self._assets:
                return self._assets[slug]
            cfg = self.get_config(slug)
            assets = CityAssets(slug=slug, config=cfg)
            self._assets[slug] = assets
            return assets

    def _download_pipeline(self, slug: str, url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading pipeline for %s from %s", slug, url)
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to download pipeline for %s: %s", slug, exc)
            raise RuntimeError(f"Could not download prediction model for {slug}") from exc

    def load_prediction_assets(self, slug: str) -> tuple[pd.DataFrame, Any]:
        """Lazy-load df.pkl + pipeline.pkl for a city. Cached after first call."""
        assets = self.get_assets(slug)
        with self._lock:
            if "prediction" in assets._loaded_flags:
                return assets.df, assets.pipeline

            city_model_dir = self.models_dir / slug
            df_path = city_model_dir / "df.pkl"
            pipeline_path = city_model_dir / "pipeline.pkl"

            if not df_path.exists():
                raise FileNotFoundError(f"{df_path} is missing")

            with open(df_path, "rb") as f:
                assets.df = pickle.load(f)
            logger.info("Loaded df.pkl for %s: shape=%s", slug, assets.df.shape)

            if not pipeline_path.exists():
                pipeline_url = assets.config.get("pipeline_url")
                if pipeline_url:
                    try:
                        self._download_pipeline(slug, pipeline_url, pipeline_path)
                    except RuntimeError:
                        # Non-fatal: the df is still loaded, so form schemas
                        # keep working; predict() will raise a clear error
                        # if someone actually tries to run a prediction.
                        pass

            if pipeline_path.exists():
                import joblib

                assets.pipeline = joblib.load(pipeline_path)
                logger.info("Loaded pipeline for %s", slug)
            else:
                logger.warning("No pipeline available for %s", slug)
                assets.pipeline = None

            assets._loaded_flags.add("prediction")
            return assets.df, assets.pipeline

    def load_analytics_assets(self, slug: str) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
        assets = self.get_assets(slug)
        with self._lock:
            if "analytics" in assets._loaded_flags:
                return assets.analytics_df, assets.wordcloud_df

            city_data_dir = self.data_dir / slug
            analytics_path = city_data_dir / "analytics.csv"
            wordcloud_path = city_data_dir / "wordcloud.csv"

            assets.analytics_df = pd.read_csv(analytics_path) if analytics_path.exists() else None
            assets.wordcloud_df = pd.read_csv(wordcloud_path) if wordcloud_path.exists() else None

            assets._loaded_flags.add("analytics")
            return assets.analytics_df, assets.wordcloud_df

    def load_recommendation_assets(self, slug: str) -> tuple[pd.DataFrame | None, Any]:
        assets = self.get_assets(slug)
        with self._lock:
            if "recommendation" in assets._loaded_flags:
                return assets.recommend_df, assets.similarity

            city_model_dir = self.models_dir / slug
            rec_path = city_model_dir / "recommend_df.pkl"
            sim_path = city_model_dir / "hybrid_similarity.pkl"

            if rec_path.exists():
                with open(rec_path, "rb") as f:
                    assets.recommend_df = pickle.load(f)
            if sim_path.exists():
                with open(sim_path, "rb") as f:
                    assets.similarity = pickle.load(f)

            assets._loaded_flags.add("recommendation")
            return assets.recommend_df, assets.similarity

    def load_market_assets(self, slug: str) -> pd.DataFrame | None:
        assets = self.get_assets(slug)
        with self._lock:
            if "market" in assets._loaded_flags:
                return assets.market_df

            path = self.data_dir / slug / "market_trends.csv"
            assets.market_df = pd.read_csv(path) if path.exists() else None

            assets._loaded_flags.add("market")
            return assets.market_df

    def warm_up(self) -> None:
    """
    Startup should ONLY discover cities.

    Do not load any dataframe, model or recommendation assets.
    Everything will be loaded lazily on first request.
    """
    self.discover_cities()
    logger.info(
        "Discovered %d cities: %s",
        len(self._configs),
        ", ".join(self._configs.keys())
    )


# Module-level singleton, imported by services/routers.
city_manager = CityManager()
