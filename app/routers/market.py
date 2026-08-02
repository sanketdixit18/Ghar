from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.routers.analytics import _require_city
from app.routers.prediction import _default_city
from app.services.loader import city_manager
from app.services.market_service import market_service

router = APIRouter(tags=["market"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/market", response_class=HTMLResponse)
async def market_page(request: Request, city: str | None = Query(default=None)):
    city = _default_city(city)
    _require_city(city)
    cfg = city_manager.get_config(city)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "city_slug": city, "cfg": cfg, "initial_tab": "market"},
    )


@router.get("/api/market/filters")
async def market_filters(city: str = Query(...)):
    city = _require_city(city)
    if not market_service.is_available(city):
        return {"available": False}
    return {"available": True, **market_service.get_filter_options(city)}


@router.get("/api/market/overview")
async def market_overview(
    city: str = Query(...),
    locality: str = Query("All"),
    builder: str = Query("All"),
    property_type: str = Query("All"),
    price_segment: str = Query("All"),
):
    city = _require_city(city)
    if not market_service.is_available(city):
        return {"available": False}
    data = market_service.get_dashboard(city, {
        "locality": locality, "builder": builder,
        "property_type": property_type, "price_segment": price_segment,
    })
    return data
