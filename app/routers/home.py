from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import APP_AUTHOR, APP_DESCRIPTION, APP_VERSION, GITHUB_URL, LINKEDIN_URL, PROJECT_METRICS, TEMPLATES_DIR
from app.models.response_models import HealthResponse
from app.services.loader import city_manager

router = APIRouter(tags=["home"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    cities = city_manager.list_cities(active_only=False)
    active_cities = [c for c in cities if c.get("status") == "active"]
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "cities": cities,
            "active_city_names": ", ".join(c["city"] for c in active_cities),
            "metrics": PROJECT_METRICS,
            "cities_covered": len(active_cities),
            "app_description": APP_DESCRIPTION,
            "author": APP_AUTHOR,
            "linkedin_url": LINKEDIN_URL,
            "github_url": GITHUB_URL,
        },
    )


@router.get("/cities")
async def cities_endpoint():
    """API: list all discovered cities (also used by the frontend nav).
    New cities are picked up automatically the moment a models/<slug>/
    folder with a config.json exists — no code change required here."""
    return city_manager.list_cities(active_only=True)


@router.get("/health", response_model=HealthResponse)
async def health():
    cities = city_manager.discover_cities()
    return HealthResponse(status="ok", version=APP_VERSION, cities_loaded=list(cities.keys()))
