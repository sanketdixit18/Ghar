from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.routers.prediction import _default_city
from app.services.analytics_service import analytics_service
from app.services.loader import city_manager

router = APIRouter(tags=["analytics"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _require_city(city: str) -> str:
    city = city.lower()
    if not city_manager.city_exists(city):
        raise HTTPException(status_code=404, detail=f"City '{city}' was not found.")
    return city


def _filters(sector: str, price_min: float | None, price_max: float | None,
             property_type: str, bedrooms: str | None) -> dict:
    return {
        "sector": sector,
        "price_min": price_min,
        "price_max": price_max,
        "property_type": property_type,
        "bedrooms": bedrooms,
    }


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, city: str | None = Query(default=None)):
    city = _default_city(city)
    _require_city(city)
    cfg = city_manager.get_config(city)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "city_slug": city, "cfg": cfg, "initial_tab": "analytics"},
    )


@router.get("/api/analytics/overview")
async def analytics_overview(
    city: str = Query(...),
    sector: str = Query("All"),
    price_min: float | None = Query(None),
    price_max: float | None = Query(None),
):
    city = _require_city(city)
    return analytics_service.get_dashboard(city, _filters(sector, price_min, price_max, "All", None))


@router.get("/sector")
async def sector_geo_map(city: str = Query(...), sector: str = Query("All"),
                          price_min: float | None = Query(None), price_max: float | None = Query(None)):
    """Sector-level geo price map (same source as the original 'Geo Map' tab)."""
    city = _require_city(city)
    data = analytics_service.get_dashboard(city, _filters(sector, price_min, price_max, "All", None))
    if not data.get("available"):
        raise HTTPException(status_code=404, detail=f"Analytics are not available for {city}.")
    return {"geo_map": data["geo_map"], "kpis": data["kpis"], "filter_options": data["filter_options"]}


@router.get("/wordcloud")
async def wordcloud(city: str = Query(...), sector: str = Query("All")):
    city = _require_city(city)
    if not analytics_service.is_available(city):
        raise HTTPException(status_code=404, detail=f"Analytics are not available for {city}.")
    image = analytics_service.get_wordcloud_image(city, sector)
    if image is None:
        return {"available": False, "image": None}
    return {"available": True, "image": image}


@router.get("/area-price")
async def area_price(city: str = Query(...), property_type: str = Query("All"), bedrooms: str = Query("All")):
    city = _require_city(city)
    data = analytics_service.get_dashboard(city, _filters("All", None, None, property_type, bedrooms))
    if not data.get("available"):
        raise HTTPException(status_code=404, detail=f"Analytics are not available for {city}.")
    return {"chart": data["area_vs_price"], "filter_options": data["filter_options"]}


@router.get("/bhk")
async def bhk_distribution(city: str = Query(...), sector: str = Query("All")):
    city = _require_city(city)
    data = analytics_service.get_dashboard(city, _filters(sector, None, None, "All", None))
    if not data.get("available"):
        raise HTTPException(status_code=404, detail=f"Analytics are not available for {city}.")
    return {"bhk_distribution": data["bhk_distribution"], "bedroom_price_box": data["bedroom_price_box"]}


@router.get("/property-type")
async def property_type_histogram(city: str = Query(...), sector: str = Query("All")):
    city = _require_city(city)
    data = analytics_service.get_dashboard(city, _filters(sector, None, None, "All", None))
    if not data.get("available"):
        raise HTTPException(status_code=404, detail=f"Analytics are not available for {city}.")
    return {"price_histogram": data["price_histogram"]}


@router.get("/locality", response_class=HTMLResponse)
async def locality_explorer(request: Request, city: str | None = Query(default=None)):
    """Location Explorer — flagged 'Coming Soon' in the original app; kept
    as a real route so it's ready to wire up once that dataset exists."""
    city = _default_city(city)
    _require_city(city)
    cfg = city_manager.get_config(city)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "city_slug": city, "cfg": cfg, "initial_tab": "locality"},
    )
