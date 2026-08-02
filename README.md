# 🏠 Real Estate Price Prediction System — FastAPI Edition

A production-ready FastAPI rewrite of the original Streamlit real estate ML
app. Same models, same preprocessing, same recommendation engine — a new,
scalable, multi-city web architecture.

## ✨ Features

- **Price Prediction** — instant ML-based price estimates with confidence range
- **Property Recommendation** — hybrid similarity engine, top-5 similar listings
- **Market Analytics** — geo price map, word cloud, area-vs-price, BHK analysis, price distribution
- **Market Trends** — builder/locality insights, RERA & construction-status breakdowns
- **Dynamic multi-city support** — add a city with zero backend code changes
- **Modern glassmorphism SaaS UI** — dark/light mode, responsive, animated

## 🏗️ Architecture

```
real-estate-app/
├── main.py                    # FastAPI entrypoint
├── requirements.txt
├── render.yaml / Procfile
├── app/
│   ├── config.py
│   ├── routers/                # home, prediction, recommendation, analytics, market
│   ├── services/                # loader (CityManager), prediction, recommendation, analytics, market
│   ├── models/                  # Pydantic v2 request/response models
│   ├── templates/                # Jinja2 (base, home, dashboard, 404, 500)
│   ├── static/{css,js}/
│   └── utils/logging_config.py
├── models/
│   ├── gurgaon/  (config.json, df.pkl, recommend_df.pkl, hybrid_similarity.pkl)
│   └── mumbai/   (config.json, df.pkl)
└── data/
    ├── gurgaon/  (analytics.csv, wordcloud.csv, market_trends.csv, recommendation.csv)
    └── mumbai/   (analytics.csv)
```

## 🌍 Adding a New City (no code changes)

1. Create `models/<city-slug>/config.json`:
   ```json
   {
     "city": "Pune",
     "state": "Maharashtra",
     "currency": "₹",
     "unit": "Cr",
     "theme": "blue",
     "emoji": "🏙️",
     "pipeline_url": "https://.../pipeline.pkl",
     "prediction_inputs": { "...": { "type": "select", "label": "..." } },
     "features": { "prediction": true, "analytics": false, "recommendation": false, "market_trends": false }
   }
   ```
2. Add `models/<city-slug>/df.pkl` (and `pipeline.pkl`, or set `pipeline_url` to download it on first use).
3. Optionally add `data/<city-slug>/analytics.csv` (+ `wordcloud.csv`, `market_trends.csv`) for analytics/market features.
4. Restart the app (or wait for the next request — city discovery re-scans automatically). Done — no router, service, or template edits required.

The `AnalyticsService` resolves column names dynamically (`COLUMN_ALIASES` in
`app/services/analytics_service.py`), so a new city's CSV doesn't need to
match Gurgaon's or Mumbai's exact schema.

## 🚀 Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit `http://localhost:8000`. Interactive API docs: `http://localhost:8000/docs`.

## ☁️ Deploying to Render

1. Push this repo to GitHub.
2. In Render, "New +" → "Blueprint" → point at this repo (`render.yaml` is auto-detected), **or** create a Web Service manually with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Set environment variables if needed (`ENVIRONMENT=production`, `LOG_LEVEL=INFO`).

## 🧪 Key API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Home page |
| GET | `/cities` | List discovered cities |
| GET | `/prediction?city=` | Prediction UI |
| POST | `/predict` | Run a prediction |
| GET | `/recommendation?city=` | Recommendation UI |
| POST | `/recommend` | Get similar properties |
| GET | `/analytics?city=` | Analytics dashboard |
| GET | `/sector` \| `/wordcloud` \| `/area-price` \| `/bhk` \| `/property-type` | Analytics chart data |
| GET | `/market?city=` | Market trends dashboard |
| GET | `/locality?city=` | Locality explorer (placeholder) |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

## ⚠️ Notes preserved from the original app

- ML models, preprocessing, and the recommendation algorithm are **unchanged** — only the application architecture was migrated.
- Gurgaon and Mumbai's `pipeline.pkl` are downloaded from a release URL on first prediction request if not already present locally (same lazy-download behavior as the Streamlit version); once downloaded they're cached in memory for the life of the process.
- Mumbai currently has no recommendation/word cloud/market-trends datasets, matching the source data — those tabs are automatically hidden for Mumbai based on `features` in its `config.json`.
