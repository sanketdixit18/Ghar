from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.models.request_models import PredictionRequest
from app.models.response_models import PredictionResponse
from app.services.loader import city_manager
from app.services.prediction_service import prediction_service

router = APIRouter(tags=["prediction"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _default_city(city: str | None) -> str:
    if city:
        return city.lower()
    active = city_manager.list_cities(active_only=True)
    if not active:
        raise HTTPException(status_code=404, detail="No cities are configured yet.")
    return active[0]["slug"]


@router.get("/prediction", response_class=HTMLResponse)
async def prediction_page(request: Request, city: str | None = Query(default=None)):
    city = _default_city(city)
    if not city_manager.city_exists(city):
        raise HTTPException(status_code=404, detail=f"City '{city}' was not found.")
    cfg = city_manager.get_config(city)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "city_slug": city, "cfg": cfg, "initial_tab": "prediction"},
    )


@router.get("/api/prediction/schema")
async def prediction_schema(city: str = Query(...)):
    city = city.lower()
    if not city_manager.city_exists(city):
        raise HTTPException(status_code=404, detail=f"City '{city}' was not found.")
    try:
        fields = prediction_service.get_form_schema(city)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"city": city, "fields": fields}


@router.post("/predict", response_model=PredictionResponse)
async def predict(payload: PredictionRequest):
    if not city_manager.city_exists(payload.city):
        raise HTTPException(status_code=404, detail=f"City '{payload.city}' was not found.")
    try:
        result = prediction_service.predict(payload.city, payload.features)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return PredictionResponse(**result)
