"""
Real Estate Price Prediction System — FastAPI entrypoint.

Run locally:
    uvicorn main:app --reload

Run in production (Render):
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import APP_DESCRIPTION, APP_NAME, APP_VERSION, DEBUG, STATIC_DIR, TEMPLATES_DIR
from app.routers import analytics, home, market, prediction, recommendation
from app.services.loader import city_manager
from app.utils.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("real_estate.startup")

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(home.router)
app.include_router(prediction.router)
app.include_router(recommendation.router)
app.include_router(analytics.router)
app.include_router(market.router)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    started = time.time()
    logger.info("Starting %s v%s ...", APP_NAME, APP_VERSION)
    city_manager.warm_up()
    logger.info(
        "Startup complete in %.2fs — cities loaded: %s",
        time.time() - started,
        list(city_manager.discover_cities().keys()),
    )


# ---------------------------------------------------------------------------
# Request logging (lightweight)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logging.getLogger("real_estate.access").info(
        "%s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, duration_ms
    )
    return response


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    accepts_html = "text/html" in request.headers.get("accept", "")
    if exc.status_code == 404 and accepts_html:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    if exc.status_code >= 500 and accepts_html:
        return templates.TemplateResponse("500.html", {"request": request}, status_code=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger("real_estate.errors").exception("Unhandled error on %s", request.url.path)
    accepts_html = "text/html" in request.headers.get("accept", "")
    if accepts_html:
        return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=DEBUG)
