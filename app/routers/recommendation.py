from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.models.request_models import RecommendationRequest
from app.models.response_models import RecommendationResponse
from app.routers.prediction import _default_city
from app.services.loader import city_manager
from app.services.recommendation_service import recommendation_service

router = APIRouter(tags=["recommendation"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/recommendation", response_class=HTMLResponse)
async def recommendation_page(request: Request, city: str | None = Query(default=None)):
    city = _default_city(city)
    if not city_manager.city_exists(city):
        raise HTTPException(status_code=404, detail=f"City '{city}' was not found.")
    cfg = city_manager.get_config(city)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "city_slug": city, "cfg": cfg, "initial_tab": "recommendation"},
    )


@router.get("/api/recommendation/properties")
async def recommendation_properties(city: str = Query(...)):
    city = city.lower()
    if not city_manager.city_exists(city):
        raise HTTPException(status_code=404, detail=f"City '{city}' was not found.")
    if not recommendation_service.is_available(city):
        return {"available": False, "properties": []}
    return {"available": True, "properties": recommendation_service.list_properties(city)}


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(payload: RecommendationRequest):
    if not city_manager.city_exists(payload.city):
        raise HTTPException(status_code=404, detail=f"City '{payload.city}' was not found.")
    if not recommendation_service.is_available(payload.city):
        raise HTTPException(status_code=503, detail=f"Recommendations are not available for {payload.city}.")
    try:
        result = recommendation_service.recommend(payload.city, payload.property_name, payload.top_n)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RecommendationResponse(**result)
