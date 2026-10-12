<div align="center">

# 🏠 Ghar — Real Estate Price Prediction & Analytics Platform

**An end-to-end, multi-city machine learning web app that predicts property prices, recommends similar listings, and visualizes market trends.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-ghar--teal.vercel.app-brightgreen?style=for-the-badge)](https://ghar-teal.vercel.app)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic_v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

[Live Demo](https://ghar-teal.vercel.app) · [API Docs](#-api-reference) · [Architecture](#%EF%B8%8F-architecture) · [Add a City](#-add-a-new-city-with-zero-code-changes)

</div>

---

## 📌 Overview

Ghar turns raw property data into decisions. Pick a city, enter property details, and get an instant ML-based price estimate with a confidence range. Explore similar listings through a hybrid recommendation engine, and dig into market analytics through interactive dashboards.

The project started as a Streamlit prototype and was **re-engineered into a production-style FastAPI service** with a layered architecture, typed request/response contracts, and a config-driven multi-city design.

> **Why it matters:** Property buyers rely on gut feel and scattered listings. Ghar gives them a data-backed price estimate, comparable properties, and market context in one place.

## ✨ Key Features

| Feature | What it does |
|---|---|
| 💰 **Price Prediction** | ML pipeline returns an instant price estimate with a confidence range |
| 🔍 **Property Recommendation** | Hybrid similarity engine returns the top-5 most similar listings |
| 📊 **Market Analytics** | Geo price map, word cloud, area-vs-price, BHK analysis, price distribution |
| 📈 **Market Trends** | Builder and locality insights, RERA and construction-status breakdowns |
| 🌍 **Multi-City Support** | Add a new city by dropping in config and data files, with no backend changes |
| 🎨 **Modern UI** | Glassmorphism design, dark/light mode, responsive and animated |

## 🖼️ Screenshots

<!-- TODO: add 3-4 screenshots to /docs and update the paths below -->
| Price Prediction | Analytics Dashboard |
|---|---|
| ![Prediction](docs/prediction.png) | ![Analytics](docs/analytics.png) |

## 🏗️ Architecture

The app follows a clean, layered design: routers handle HTTP, services hold business logic, and Pydantic models define the contracts.

```
Ghar/
├── main.py                     # FastAPI entrypoint
├── requirements.txt
├── render.yaml / Procfile      # Deployment config
├── app/
│   ├── config.py
│   ├── routers/                # home, prediction, recommendation, analytics, market
│   ├── services/               # CityManager, prediction, recommendation, analytics, market
│   ├── models/                 # Pydantic v2 request/response schemas
│   ├── templates/              # Jinja2 (base, home, dashboard, 404, 500)
│   ├── static/{css,js}/
│   └── utils/logging_config.py
├── models/                     # Per-city ML artifacts + config.json
│   ├── gurgaon/
│   └── mumbai/
└── data/                       # Per-city analytics datasets
    ├── gurgaon/
    └── mumbai/
```

### Design decisions worth noting

- **Separation of concerns:** routers, services, and schemas are independent, which keeps each layer testable.
- **Config-driven multi-city engine:** `CityManager` auto-discovers cities from the `models/` folder. Feature flags in each city's `config.json` automatically show or hide UI tabs.
- **Schema-tolerant analytics:** `AnalyticsService` resolves column names through `COLUMN_ALIASES`, so a new city's CSV doesn't have to match an existing schema.
- **Lazy model loading:** large pipeline files are downloaded on first prediction and cached in memory for the life of the process, which keeps the repo and cold-start light.
- **Typed contracts:** Pydantic v2 validates every request and response.

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, Pydantic v2
- **ML / Data:** scikit-learn pipelines, pandas, NumPy
- **Frontend:** Jinja2 templates, HTML/CSS/JavaScript
- **Deployment:** Vercel (live demo), Render (blueprint included via `render.yaml`)

## 🌍 Add a New City with Zero Code Changes

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
  "features": {
    "prediction": true,
    "analytics": false,
    "recommendation": false,
    "market_trends": false
  }
}
```

2. Add `models/<city-slug>/df.pkl` (plus `pipeline.pkl`, or set `pipeline_url` to fetch it on first use).
3. Optionally add `data/<city-slug>/analytics.csv` (and `wordcloud.csv`, `market_trends.csv`).
4. Restart, or just make the next request. The new city shows up automatically.

## 🚀 Getting Started

```bash
# 1. Clone
git clone https://github.com/sanketdixit18/Ghar.git
cd Ghar

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
uvicorn main:app --reload
```

Open **http://localhost:8000**. Interactive API docs are at **http://localhost:8000/docs**.

## 🔌 API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Home page |
| `GET` | `/cities` | List discovered cities |
| `GET` | `/prediction?city=` | Prediction UI |
| `POST` | `/predict` | Run a price prediction |
| `GET` | `/recommendation?city=` | Recommendation UI |
| `POST` | `/recommend` | Get similar properties |
| `GET` | `/analytics?city=` | Analytics dashboard |
| `GET` | `/sector` · `/wordcloud` · `/area-price` · `/bhk` · `/property-type` | Chart data endpoints |
| `GET` | `/market?city=` | Market trends dashboard |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

## ☁️ Deployment

**Render:** use "New + → Blueprint" and point it at this repo (`render.yaml` is auto-detected), or create a web service manually:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Optional env vars: `ENVIRONMENT=production`, `LOG_LEVEL=INFO`.

## 📊 Model Performance

<!-- TODO: fill in from your notebooks -->
| City | Model | R² | MAE |
|---|---|---|---|
| Gurgaon | _your model_ | _x.xx_ | _x.xx Cr_ |
| Mumbai | _your model_ | _x.xx_ | _x.xx Cr_ |

## 🗺️ Roadmap

- [ ] Locality explorer (currently a placeholder)
- [ ] Recommendation, word cloud, and market-trend data for Mumbai
- [ ] Add more cities (Pune, Bangalore, Hyderabad)
- [ ] Unit and API tests with CI via GitHub Actions
- [ ] Dockerize for one-command deployment

## 👤 Author

**Sanket Dixit** — Computer Engineering student (Data Science & Analytics), open to Data Science / ML / GenAI roles.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/sanket-dixit-85983a243)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)](https://github.com/sanketdixit18)

---

<div align="center">⭐ If you found this useful, consider starring the repo!</div>
