import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import argparse
import logging
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(force_terminal=True)

import config
from src.db import db
from src.etl import etl_pipeline
from src.analytics import analytics_engine
from src.ml_models import ml_hub


def run_etl():
    """Runs the high-performance ETL ingestion pipeline."""
    etl_pipeline.run_ingestion()

def run_analytics():
    """Runs executive KPI and analytical query reports."""
    analytics_engine.print_analytics_report()

def run_ml():
    """Runs Machine Learning models and outputs results."""
    console.print("\n[bold magenta]🤖 Running Machine Learning Models...[/bold magenta]\n")
    
    # 1. RFM
    console.print("[bold cyan]1. Customer RFM Segmentation (K-Means Clustering)[/bold cyan]")
    rfm_res = ml_hub.run_rfm_segmentation()
    if rfm_res.get("status") == "success":
        rfm_table = Table(header_style="bold green")
        rfm_table.add_column("Customer Segment", style="cyan")
        rfm_table.add_column("Customer Count", justify="right", style="white")
        rfm_table.add_column("Share %", justify="right", style="yellow")
        rfm_table.add_column("Avg Spend ($)", justify="right", style="green")
        rfm_table.add_column("Avg Recency (Days)", justify="right", style="magenta")

        for seg in rfm_res["segments"]:
            rfm_table.add_row(
                seg["segment"],
                f"{seg['customer_count']:,}",
                f"{seg['percentage']}%",
                f"${seg['avg_monetary_spend']:,.2f}",
                f"{seg['avg_recency_days']}d",
            )
        console.print(rfm_table)
    else:
        console.print(f"[red]RFM Failed: {rfm_res.get('message')}[/red]")

    # 2. Sales Forecasting
    console.print("\n[bold cyan]2. 6-Month Sales & Revenue Time-Series Forecast[/bold cyan]")
    forecast_res = ml_hub.run_sales_forecast()
    if forecast_res.get("status") == "success":
        f_table = Table(header_style="bold magenta")
        f_table.add_column("Future Month", style="cyan")
        f_table.add_column("Predicted Sales ($)", justify="right", style="bold green")
        f_table.add_column("Lower 95% Bound ($)", justify="right", style="dim")
        f_table.add_column("Upper 95% Bound ($)", justify="right", style="dim")

        for f in forecast_res["forecast"]:
            f_table.add_row(
                f["month"],
                f"${f['predicted_sales']:,.2f}",
                f"${f['lower_bound']:,.2f}",
                f"${f['upper_bound']:,.2f}",
            )
        console.print(f_table)
        console.print(f"[green]Projected Growth: {forecast_res.get('projected_growth_pct')}%[/green]\n")
    else:
        console.print(f"[red]Forecast Failed: {forecast_res.get('message')}[/red]")

def start_server():
    """Launches the interactive FastAPI dashboard server."""
    console.print(f"\n[bold green]🌐 Starting PySQL-Sync Web Dashboard on http://{config.SERVER_HOST}:{config.SERVER_PORT}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop the server.[/dim]\n")
    uvicorn.run("web.app:app", host=config.SERVER_HOST, port=config.SERVER_PORT, reload=False)

def interactive_menu():
    """Displays interactive CLI menu."""
    banner = Panel.fit(
        "[bold cyan]PySQL-Sync (Retailytics Pro)[/bold cyan]\n"
        "[dim]High-Performance Data Engineering, Analytics & ML Platform[/dim]\n"
        f"[green]Database Engine: {db.db_type.upper()}[/green]",
        border_style="cyan"
    )
    console.print(banner)

    console.print("\n[bold]Select an action:[/bold]")
    console.print("  [bold cyan]1[/bold cyan] - Run High-Speed Batch Ingestion (ETL)")
    console.print("  [bold cyan]2[/bold cyan] - Run Business Analytics & KPI Report")
    console.print("  [bold cyan]3[/bold cyan] - Run Machine Learning Models (RFM & Forecasting)")
    console.print("  [bold cyan]4[/bold cyan] - Launch Interactive Web Dashboard")
    console.print("  [bold cyan]5[/bold cyan] - Run All (ETL + Analytics + ML)")
    console.print("  [bold cyan]0[/bold cyan] - Exit\n")

    choice = input("Enter choice (1-5): ").strip()
    if choice == "1":
        run_etl()
    elif choice == "2":
        run_analytics()
    elif choice == "3":
        run_ml()
    elif choice == "4":
        start_server()
    elif choice == "5":
        run_etl()
        run_analytics()
        run_ml()
    else:
        console.print("[yellow]Exiting PySQL-Sync.[/yellow]")

def main():
    parser = argparse.ArgumentParser(description="PySQL-Sync (Retailytics Pro) Unified CLI Runner")
    parser.add_argument("--etl", action="store_true", help="Run high-speed batch ETL pipeline")
    parser.add_argument("--analytics", action="store_true", help="Run executive KPIs and analytical queries")
    parser.add_argument("--ml", action="store_true", help="Run RFM segmentation and sales forecasting")
    parser.add_argument("--serve", action="store_true", help="Start interactive web dashboard server")
    parser.add_argument("--all", action="store_true", help="Run complete pipeline (ETL + Analytics + ML)")

    args = parser.parse_args()

    if args.etl:
        run_etl()
    elif args.analytics:
        run_analytics()
    elif args.ml:
        run_ml()
    elif args.serve:
        start_server()
    elif args.all:
        run_etl()
        run_analytics()
        run_ml()
    else:
        if sys.stdin.isatty():
            interactive_menu()
        else:
            # Default non-interactive run
            run_analytics()

if __name__ == "__main__":
    main()
