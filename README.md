# 🏠 Ghar — Real Estate Price Prediction & Analytics Platform

**An end-to-end Machine Learning application for real estate price prediction, property recommendations, and market analytics across multiple cities.**

<p align="center">
  <a href="https://ghar-teal.vercel.app/"><strong>🚀 Live Demo</strong></a> •
  <a href="https://github.com/sanketdixit18/Ghar"><strong>💻 Source Code</strong></a> •
  <a href="https://ghar-teal.vercel.app/docs"><strong>📚 API Documentation</strong></a>
</p>

---

## 📌 Overview

**Ghar** transforms residential property data into actionable insights using Machine Learning and interactive analytics.

The platform enables users to estimate property prices, discover similar properties, and explore real estate market patterns through data-driven visualizations. It currently supports **Mumbai and Gurgaon**, with a configuration-driven architecture designed to simplify the addition of new cities.

Unlike a notebook-only ML project, Ghar integrates the complete workflow—from model inference and data processing to API development, analytics, and web deployment.

### 🎯 Problem Statement

Real estate buyers and investors often face difficulties estimating fair property prices and understanding locality-level market patterns. Ghar addresses this challenge by bringing price prediction, property discovery, and market analytics together in one application.

## ✨ Key Features

### 💰 1. Machine Learning-Based Price Prediction
- Predict residential property prices from structured property features.
- Use a trained Scikit-learn Decision Tree Regression pipeline.
- Apply consistent preprocessing and feature transformations before inference.
- Return predictions through a web interface and API.

### 🔍 2. Similar Property Recommendations
- Discover comparable properties using a hybrid similarity-based recommendation approach.
- Help users explore alternatives based on property characteristics.
- Support data-driven property discovery beyond individual price estimates.

### 📊 3. Interactive Real Estate Analytics
- Explore property price distributions and area-versus-price relationships.
- Analyze bedroom configurations and property categories.
- Visualize geographic price patterns and locality-level insights.
- Use interactive dashboards to investigate market data.

### 📈 4. Market Trends
- Explore available builder, locality, and property-status insights.
- Analyze market patterns using structured property datasets.
- Present data in a format that supports easier comparison and exploration.

### 🌆 5. Configuration-Driven Multi-City Architecture
- Supports Mumbai and Gurgaon.
- Separates city-specific model artifacts, configuration, and analytics datasets.
- Uses a city management layer to discover supported cities.
- Makes future expansion possible without rewriting the core application.

### ⚙️ 6. API-Driven Application
- Built using FastAPI with typed request and response validation.
- Separates routing, business logic, and data validation.
- Includes interactive API documentation and a health-check endpoint.
- Supports deployment as a web application.

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Machine Learning | Scikit-learn, Decision Tree Regression |
| Data Processing | Pandas, NumPy |
| Model Persistence | Joblib / serialized model artifacts |
| Backend | FastAPI, Uvicorn |
| Validation | Pydantic |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| Data Visualization | Interactive analytics and charts |
| Deployment | Vercel / Render configuration |
| Version Control | Git, GitHub |

## 🧠 Machine Learning Workflow

The prediction workflow follows these stages:

1. **Data preparation:** Work with structured real estate datasets and prepare relevant property features.
2. **Preprocessing:** Apply the transformations required by the trained ML pipeline.
3. **Model training:** Train a Decision Tree Regression model for property price estimation.
4. **Evaluation:** Evaluate predictive performance using regression metrics.
5. **Model persistence:** Save the trained pipeline for reuse during inference.
6. **API integration:** Load the model pipeline and serve predictions through FastAPI.
7. **Deployment:** Expose the application through a hosted web interface.

## 🏗️ System Architecture

```text
                 User / Web Interface
                          |
                          v
                    FastAPI Backend
                          |
             +------------+------------+
             |            |            |
             v            v            v
         Prediction   Recommendation  Analytics
          Service       Service       Service
             |            |            |
             v            v            v
        ML Pipeline   Similarity     City-Specific
        & Features     Engine       Data / Datasets
             |            |            |
             +------------+------------+
                          |
                          v
                 Results & Visualizations
```

The architecture separates API routes, service logic, request/response schemas, and city-specific resources. This improves maintainability and makes the application easier to extend.

## 📂 Project Structure

```text
Ghar/
├── app/
│   ├── routers/             # API endpoints and page routes
│   ├── services/            # Prediction, analytics and recommendations
│   ├── models/              # Request and response schemas
│   ├── templates/           # HTML templates
│   ├── static/              # CSS and JavaScript assets
│   ├── config.py            # Application configuration
│   └── utils/               # Logging and utilities
├── data/
│   ├── mumbai/              # Mumbai analytics data
│   └── gurgaon/             # Gurgaon analytics data
├── models/
│   ├── mumbai/              # City-specific model resources
│   └── gurgaon/             # City-specific model resources
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── render.yaml              # Deployment configuration
├── Procfile                 # Process configuration
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or a compatible Python version.
- Git.
- pip.

### 1. Clone the repository

```bash
git clone https://github.com/sanketdixit18/Ghar.git
cd Ghar
```

### 2. Create a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the application

```bash
uvicorn main:app --reload
```

Open the application at:

- Web application: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

**Note:** Model artifacts and city-specific datasets must be available at the locations expected by the application configuration.

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application home page |
| GET | `/cities` | List supported cities |
| GET | `/prediction?city=mumbai` | Open the prediction interface |
| POST | `/predict` | Generate a property price prediction |
| GET | `/recommendation?city=mumbai` | Open property recommendations |
| POST | `/recommend` | Retrieve similar properties |
| GET | `/analytics?city=mumbai` | Open the analytics dashboard |
| GET | `/market?city=mumbai` | Explore market trends |
| GET | `/health` | Check application health |
| GET | `/docs` | Explore API documentation |

For the complete request and response schemas, run the application and visit `/docs`.

## 📈 Model Performance

The project evaluation reported the following results:

| Metric | Reported Result |
|---|---:|
| R² Score | 97.8% |
| Mean Absolute Error (MAE) | Approximately ₹18 lakhs |

**Interpretation:** The reported R² indicates a strong fit on the evaluated dataset. MAE represents the average absolute prediction error in the target price's units.

These results should be interpreted in the context of the evaluation split, dataset quality, and generalization to unseen properties. They are not a guarantee of real-world valuation accuracy.

## 🌍 Extensibility: Adding Another City

Ghar uses a configuration-driven approach to support future expansion.

At a high level, adding a city involves:

1. Creating a city-specific configuration.
2. Providing the corresponding trained model pipeline and required property data.
3. Configuring the prediction inputs and available features.
4. Adding analytics datasets when the corresponding dashboards are enabled.
5. Verifying the new city through the application and API.

This design reduces the need to duplicate the core prediction and analytics logic for every new market.

## 🔮 Potential Improvements

- Automated model retraining and experiment tracking.
- Automated testing and CI/CD integration.
- Monitoring prediction quality and data drift.
- Broader geographic coverage and refreshed datasets.
- Improved model interpretability and uncertainty estimation.
- API performance testing and structured application monitoring.

## 👨‍💻 Author

**Sanket Dixit**

Computer Engineering | Data Science | Machine Learning

- GitHub: [@sanketdixit18](https://github.com/sanketdixit18)
- Project: [Ghar — Real Estate Price Prediction & Analytics Platform](https://github.com/sanketdixit18/Ghar)
- Live Demo: [Try Ghar](https://ghar-teal.vercel.app/)

---

⭐ If you find this project interesting, consider starring the repository.

*Built to demonstrate applied Machine Learning, API development, data analytics, and maintainable application architecture.*
