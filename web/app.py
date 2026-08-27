import io
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import config
from src.db import db
from src.etl import etl_pipeline
from src.analytics import analytics_engine
from src.ml_models import ml_hub
from src.ai_assistant import ai_assistant
from src.geo import geo_service
from src.report_generator import report_generator

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

def auto_seed_database_if_empty():
    """Runs ingestion automatically in background on server boot if tables are empty."""
    try:
        table_stats = etl_pipeline.get_database_stats()
        total_rows = sum(item.get("count", 0) for item in table_stats)
        if total_rows == 0:
            print("[PySQL-Sync] Empty database detected on startup. Auto-seeding tables in background...")
            etl_pipeline.run_ingestion()
            print("[PySQL-Sync] Auto-seeding completed successfully!")
    except Exception as err:
        print(f"[PySQL-Sync] Auto-seed background notice: {err}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed in background on startup
    threading.Thread(target=auto_seed_database_if_empty, daemon=True).start()
    yield

app = FastAPI(
    title="PySQL-Sync (Retailytics Pro)",
    description="E-Commerce Data Integration, Analytics & Machine Learning Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for decoupled frontend deployment
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "PySQL-Sync API",
        "version": "2.0.0",
        "database": db.db_type
    }

class CustomQueryRequest(BaseModel):
    query: str

def clean_records(df: pd.DataFrame):
    """Converts DataFrame to records list, replacing NaN/NaT with None for JSON compliance."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        return []
    return json.loads(df.to_json(orient="records"))

# ------------------------------------------------------------------------------
# Page Routes
# ------------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "db_type": db.db_type.upper(),
            "version": "2.0.0",
        }
    )

# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------
@app.get("/api/status")
async def get_system_status():
    is_connected, status_msg = db.check_connection()
    table_stats = etl_pipeline.get_database_stats()
    total_rows = sum(item["count"] for item in table_stats)
    return {
        "db_type": db.db_type.upper(),
        "connected": is_connected,
        "status_message": status_msg,
        "total_tables": len(table_stats),
        "total_records": total_rows,
        "tables": table_stats,
    }

@app.post("/api/etl/run")
async def trigger_etl(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(etl_pipeline.run_ingestion)
        return {
            "status": "success",
            "message": "Batch ingestion started in background. Tables will populate within ~20 seconds."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kpis")
async def get_kpis():
    return analytics_engine.get_kpi_summary()

@app.get("/api/analytics/overview")
async def get_analytics_overview():
    try:
        monthly_sales = analytics_engine.get_cumulative_monthly_sales()
        state_counts = analytics_engine.get_customer_counts_by_state(10)
        categories = analytics_engine.get_sales_per_category(8)
        yoy = analytics_engine.get_yoy_growth()
        installment_pct = analytics_engine.get_installment_percentage()
        corr = analytics_engine.get_price_volume_correlation()

        return {
            "monthly_sales": clean_records(monthly_sales),
            "state_distribution": clean_records(state_counts),
            "top_categories": clean_records(categories),
            "yoy_growth": clean_records(yoy),
            "installment_pct": installment_pct,
            "correlation": corr,
        }
    except Exception as e:
        return {
            "monthly_sales": [],
            "state_distribution": [],
            "top_categories": [],
            "yoy_growth": [],
            "installment_pct": 0,
            "correlation": {"correlation": 0, "sample_size": 0},
            "status": "initializing"
        }

@app.get("/api/analytics/query/{query_id}")
async def run_specific_query(query_id: int):
    try:
        if query_id == 1:
            df = analytics_engine.get_unique_cities(100)
        elif query_id == 2:
            return {"query_id": 2, "title": "Orders in 2017", "result": analytics_engine.get_orders_2017()}
        elif query_id == 3:
            df = analytics_engine.get_sales_per_category(20)
        elif query_id == 4:
            return {"query_id": 4, "title": "Installment Orders %", "result": analytics_engine.get_installment_percentage()}
        elif query_id == 5:
            df = analytics_engine.get_customer_counts_by_state(30)
        elif query_id == 6:
            df = analytics_engine.get_monthly_orders_2018()
        elif query_id == 7:
            df = analytics_engine.get_avg_products_per_order_by_city(20)
        elif query_id == 8:
            df = analytics_engine.get_category_revenue_distribution(20)
        elif query_id == 9:
            return {"query_id": 9, "title": "Price vs Purchase Correlation", "result": analytics_engine.get_price_volume_correlation()}
        elif query_id == 10:
            df = analytics_engine.get_seller_rankings(20)
        elif query_id == 11:
            df = analytics_engine.get_customer_moving_avg(30)
        elif query_id == 12:
            df = analytics_engine.get_cumulative_monthly_sales()
        elif query_id == 13:
            df = analytics_engine.get_yoy_growth()
        elif query_id == 14:
            df = analytics_engine.get_top_spending_customers()
        else:
            raise HTTPException(status_code=404, detail="Query ID not found (1-14)")

        return {
            "query_id": query_id,
            "columns": df.columns.tolist(),
            "data": clean_records(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sql/run")
async def execute_custom_sql(payload: CustomQueryRequest):
    query = payload.query.strip()
    # Basic safety check
    forbidden = ["drop", "truncate", "delete", "alter", "shutdown"]
    if any(query.lower().startswith(word) for word in forbidden):
        raise HTTPException(status_code=400, detail="Data modification queries are restricted in read-only Studio.")

    try:
        df = db.execute_query(query)
        return {
            "status": "success",
            "row_count": len(df),
            "columns": df.columns.tolist(),
            "data": clean_records(df.head(200))
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class AIQueryRequest(BaseModel):
    prompt: str

@app.post("/api/ai/ask")
async def ask_ai_assistant(payload: AIQueryRequest):
    return ai_assistant.process_query(payload.prompt)

@app.get("/api/geo/density")
async def get_geo_density():
    return geo_service.get_state_sales_density()

@app.get("/api/geo/routes")
async def get_geo_routes():
    return geo_service.get_top_logistics_routes(8)

@app.get("/api/ml/rfm")
async def get_rfm_segments():
    return ml_hub.run_rfm_segmentation()

@app.get("/api/ml/forecast")
async def get_sales_forecast():
    return ml_hub.run_sales_forecast(6)

@app.get("/api/ml/basket")
async def get_market_basket():
    return ml_hub.run_market_basket_analysis()

@app.get("/api/ml/delay")
async def get_logistics_delay():
    return ml_hub.get_logistics_delay_analysis()

@app.get("/api/ml/clv")
async def get_clv_and_churn():
    return ml_hub.get_clv_and_churn_analysis()

@app.get("/api/export/pdf")
async def export_executive_pdf():
    try:
        pdf_stream = report_generator.generate_pdf_report()
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=retailytics_executive_report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/csv/{query_id}")
async def export_query_csv(query_id: int):
    try:
        if query_id == 1:
            df = analytics_engine.get_unique_cities(1000)
        elif query_id == 3:
            df = analytics_engine.get_sales_per_category(100)
        elif query_id == 5:
            df = analytics_engine.get_customer_counts_by_state(100)
        elif query_id == 10:
            df = analytics_engine.get_seller_rankings(100)
        elif query_id == 13:
            df = analytics_engine.get_yoy_growth()
        elif query_id == 14:
            df = analytics_engine.get_top_spending_customers()
        else:
            df = analytics_engine.get_sales_per_category(100)

        csv_content = df.to_csv(index=False)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=query_{query_id}_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
