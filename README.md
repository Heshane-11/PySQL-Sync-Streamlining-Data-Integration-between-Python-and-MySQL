# ⚡ PySQL-Sync (Retailytics Enterprise Platform)

[![Live Frontend (Vercel)](https://img.shields.io/badge/Live%20Demo-Vercel%20Frontend-black.svg?logo=vercel&logoColor=white)](https://py-sql-sync-streamlining-data-integ-eta.vercel.app)
[![Live Backend (Render)](https://img.shields.io/badge/Live%20API-Render%20Cloud-46E3B7.svg?logo=render&logoColor=white)](https://retailytics-m48i.onrender.com)
[![API Docs](https://img.shields.io/badge/Swagger-API%20Documentation-85EA2D.svg?logo=swagger&logoColor=black)](https://retailytics-m48i.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Zero--Config-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Leaflet](https://img.shields.io/badge/Leaflet-Maps-199900.svg?logo=leaflet&logoColor=white)](https://leafletjs.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-25%2F25%20Passing-brightgreen.svg)]()

> **Enterprise E-Commerce Data Engineering, Schema-Aware RAG AI Assistant, Geospatial Analytics, Predictive Machine Learning & Decoupled Cloud Web Platform.**

---

## 🌐 Live Cloud Deployments

| Service | Hosting Provider | Live URL | Description |
| :--- | :--- | :--- | :--- |
| **🎨 Web Dashboard (Frontend)** | **Vercel** | **[Launch App ➔](https://py-sql-sync-streamlining-data-integ-eta.vercel.app)** | Glassmorphic Dark-Mode UI with dynamic charts, Leaflet map, and AI query assistant. |
| **⚡ REST API (Backend)** | **Render** | **[API Endpoint ➔](https://retailytics-m48i.onrender.com)** | High-speed FastAPI engine with multi-dialect support (SQLite/MySQL) & CORS enabled. |
| **📖 Interactive API Docs** | **Render Swagger** | **[Open Swagger UI ➔](https://retailytics-m48i.onrender.com/docs)** | Interactive Swagger / OpenAPI documentation for all analytical endpoints. |

---

## 🌟 Key Features Matrix

| Module | Features & Capabilities |
| :--- | :--- |
| **🤖 AI Text-to-SQL (RAG)** | Natural language questioning with **Schema-Aware RAG**, multi-lingual / Hinglish slot extraction, automatic SQL generation, query execution & human-friendly business insights. |
| **🗺️ Geospatial Maps** | Interactive **Leaflet.js** map visualizing customer concentration, revenue density across all 27 Brazilian states & logistics fulfillment routes with zero watermarks. |
| **🚚 Logistics Delay ML** | Evaluates transit times, computes national on-time delivery rate (**92.16%** vs **7.84% delay rate**), and ranks states by shipping risk. |
| **👥 CLV & Churn Engine** | Predicts 12-Month **Customer Lifetime Value (CLV)** and computes Churn Probability risk scoring across customer cohorts. |
| **📊 SQL Analytics** | 14 core optimized queries + executive KPI metrics (**$16.01M Gross Sales**, **99.4K Orders**, **96.1K Customers**, **$154.10 AOV**, YoY Growth). |
| **🤖 Unsupervised ML** | **RFM Customer Segmentation (K-Means)** (Champions, Loyal, Potential, At-Risk) + 6-Month **Sales Time-Series Forecast (95% CI)** + **Market Basket Analysis**. |
| **📄 1-Click PDF Exporter** | Branded executive PDF brief generation (`reportlab`) with tables & KPI summaries + instant CSV downloads. |
| **⚡ High-Speed Batch ETL** | Ingests & indexes **1.45+ Million records** in **<25 seconds** (**75,000+ rows/sec**) with memory-safe chunked streaming for cloud tiers. |
| **🐳 Dockerized** | Complete `Dockerfile` and `docker-compose.yml` for 1-command deployment. |

---

## 🏗️ Architecture & Decoupled Directory Structure

```text
PySQL-Sync/
├── config.py                 # Configuration & settings manager
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies (fastapi, scikit-learn, reportlab, etc.)
├── main.py                   # Unified CLI runner (--etl, --analytics, --ml, --serve, --all)
├── Dockerfile                # Production Docker container definition
├── docker-compose.yml        # Multi-container orchestration (FastAPI + MySQL 8.0)
├── Procfile                  # Render / Railway process definition
├── render.yaml               # Render Infrastructure-as-Code blueprint
├── railway.json              # Railway deployment config
├── fly.toml                  # Fly.io deployment config
│
├── frontend/                 # 🌐 Decoupled Standalone Frontend (Vercel / Netlify)
│   ├── index.html            # Standalone Single-Page Application UI
│   ├── css/style.css         # Glassmorphic dark-mode styling
│   ├── js/dashboard.js       # Dynamic API resolver, Leaflet map, charts & AI assistant
│   ├── vercel.json           # Vercel deployment configuration
│   └── netlify.toml          # Netlify deployment configuration
│
├── src/                      # ⚙️ Core Backend Business Logic
│   ├── db.py                 # Connection pooling & multi-dialect SQL engine (MySQL + SQLite)
│   ├── etl.py                # Memory-safe batch ETL pipeline & index generator
│   ├── ai_assistant.py       # AI Text-to-SQL Assistant with Schema-Aware RAG
│   ├── geo.py                # Geospatial state density and shipping routes service
│   ├── analytics.py          # 14 business queries & executive KPI engine
│   ├── ml_models.py          # RFM, Sales Forecast, Market Basket, Delay ML, CLV
│   ├── report_generator.py   # Executive PDF report generator
│   └── queries.sql           # Documented raw SQL scripts
│
├── web/                      # 🚀 FastAPI REST API Backend
│   ├── app.py                # FastAPI app with CORS middleware, lifespan auto-seeder & REST endpoints
│   ├── static/               # Static assets for monolithic fallback mode
│   └── templates/            # Jinja2 templates
│
└── tests/                    # 🧪 25/25 Passing Automated Unit Tests
    ├── test_db.py
    ├── test_etl.py
    ├── test_analytics.py
    ├── test_ml.py
    ├── test_ai.py
    ├── test_geo.py
    ├── test_pdf.py
    ├── test_hinglish.py
    └── test_universal_ai.py
```

---

## 🚀 Quick Start Guide

### 1. Run Locally
```bash
# 1. Clone repository
git clone https://github.com/Heshane-11/PySQL-Sync-Streamlining-Data-Integration-between-Python-and-MySQL.git
cd PySQL-Sync-Streamlining-Data-Integration-between-Python-and-MySQL

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Start Backend Server & Web UI
python main.py --serve
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

### 2. Run via Docker Compose
```bash
docker-compose up --build
```

---

## 🧪 Automated Testing
```bash
python -m pytest tests/ -v
```
All **25/25 automated unit tests** verify database connectivity, ETL cleaning, AI schema RAG, geospatial services, machine learning models, and PDF creation.

---

## 📄 License
This project is licensed under the MIT License.
