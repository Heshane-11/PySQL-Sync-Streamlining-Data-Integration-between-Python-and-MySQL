# ⚡ PySQL-Sync (Retailytics Enterprise Platform)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Zero--Config-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Leaflet](https://img.shields.io/badge/Leaflet-Maps-199900.svg?logo=leaflet&logoColor=white)](https://leafletjs.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-10%2F10%20Passing-brightgreen.svg)]()

> **Enterprise E-Commerce Data Engineering, Schema-Aware RAG AI Assistant, Geospatial Analytics, Predictive Machine Learning & Interactive Web Intelligence Platform.**

---

## 🌟 Key Features Matrix

| Module | Features & Capabilities |
| :--- | :--- |
| **🤖 AI Text-to-SQL (RAG)** | Natural language questioning with **Schema-Aware RAG**, automated SQL generation, query execution & human-friendly business insights. |
| **🗺️ Geospatial Maps** | Interactive **Leaflet.js** map visualizing customer concentration, revenue density across all 27 Brazilian states & logistics fulfillment routes. |
| **🚚 Logistics Delay ML** | Evaluates transit times, computes national on-time vs delay rates (7.8% delay rate), and ranks states by shipping risk. |
| **👥 CLV & Churn Engine** | Predicts 12-Month **Customer Lifetime Value (CLV)** and computes Churn Probability scoring across customer cohorts. |
| **📊 SQL Analytics** | 14 core queries + executive KPI metrics (Gross Sales, Orders, AOV, YoY Growth). |
| **🤖 Unsupervised ML** | **RFM Customer Segmentation (K-Means)** (Champions, Loyal, Potential, At-Risk) + 6-Month **Sales Time-Series Forecast**. |
| **📄 1-Click PDF Exporter** | Branded executive PDF brief generation (`reportlab`) with tables & KPI summaries + instant CSV downloads. |
| **⚡ High-Speed ETL** | Ingests & indexes **1.45+ Million records** in **~23-39 seconds** with multi-dialect support (MySQL & SQLite fallback). |
| **🐳 Dockerized** | Complete `Dockerfile` and `docker-compose.yml` for 1-command deployment. |

---

## 🏗️ Architecture

```text
PySQL-Sync/
├── config.py                 # Configuration & settings manager
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── main.py                   # Unified CLI runner
├── Dockerfile                # Production Docker container definition
├── docker-compose.yml        # Multi-container orchestration (App + MySQL 8.0)
│
├── src/
│   ├── __init__.py
│   ├── db.py                 # DB connection manager (MySQL + SQLite multi-dialect)
│   ├── etl.py                # Fast batch ETL pipeline & index generator
│   ├── ai_assistant.py       # AI Text-to-SQL Assistant with Schema-Aware RAG
│   ├── geo.py                # Geospatial state density and shipping routes service
│   ├── analytics.py          # 14 business queries & executive KPI engine
│   ├── ml_models.py          # RFM, Sales Forecast, Market Basket, Delay ML, CLV
│   ├── report_generator.py   # Executive PDF report generator
│   └── queries.sql           # Documented raw SQL scripts
│
├── web/
│   ├── app.py                # FastAPI web backend with full REST API
│   ├── static/
│   │   ├── css/style.css     # Glassmorphic dark-mode design system
│   │   └── js/dashboard.js   # Dynamic charts, Leaflet maps, AI assistant handler
│   └── templates/
│       └── index.html        # Interactive Enterprise Dashboard UI
│
└── tests/                    # 10/10 Passing Automated Unit Tests
    ├── test_db.py
    ├── test_etl.py
    ├── test_analytics.py
    ├── test_ml.py
    ├── test_ai.py
    ├── test_geo.py
    └── test_pdf.py
```

---

## 🚀 Quick Start Guide

### 1. Run Locally
```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Start Web Dashboard
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
All 10/10 tests verify database connectivity, ETL cleaning, AI schema RAG, geospatial services, machine learning models, and PDF creation.
