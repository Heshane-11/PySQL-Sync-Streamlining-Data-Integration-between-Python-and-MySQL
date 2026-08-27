import os
import time
import logging
from typing import Dict, Any, List
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import config
from src.db import db

logger = logging.getLogger(__name__)
console = Console(force_terminal=True)

class ETLPipeline:
    def __init__(self):
        self.data_dir = config.DATA_DIR
        self.chunk_size = config.BATCH_CHUNK_SIZE

    def clean_dataframe(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Sanitizes columns, converts datatypes, and handles null values."""
        # 1. Clean Column Names
        df.columns = [
            col.strip().replace(" ", "_").replace("-", "_").replace(".", "_").lower()
            for col in df.columns
        ]

        # 2. Fix known column variations (e.g., product category)
        if "product_category" in df.columns and "product_category_name" not in df.columns:
            df.rename(columns={"product_category": "product_category_name"}, inplace=True)

        # 3. Parse Datetime columns for specific tables
        datetime_cols = {
            "orders": [
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
            "order_items": ["shipping_limit_date"],
        }

        if table_name in datetime_cols:
            for col in datetime_cols[table_name]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        # 4. Handle Missing Values
        # For object types, ensure strings or None; numeric retains NaN for SQL NULL
        return df

    def create_indexes(self):
        """Creates indexes on frequently queried and joined columns for fast queries."""
        indexes = [
            ("idx_customers_id", "customers", "customer_id"),
            ("idx_customers_city", "customers", "customer_city"),
            ("idx_customers_state", "customers", "customer_state"),
            ("idx_orders_id", "orders", "order_id"),
            ("idx_orders_customer_id", "orders", "customer_id"),
            ("idx_orders_timestamp", "orders", "order_purchase_timestamp"),
            ("idx_order_items_order_id", "order_items", "order_id"),
            ("idx_order_items_product_id", "order_items", "product_id"),
            ("idx_order_items_seller_id", "order_items", "seller_id"),
            ("idx_products_id", "products", "product_id"),
            ("idx_payments_order_id", "payments", "order_id"),
            ("idx_payments_type", "payments", "payment_type"),
            ("idx_sellers_id", "sellers", "seller_id"),
        ]

        logger.info("Creating database indexes for query acceleration...")
        for idx_name, tbl_name, col_name in indexes:
            try:
                db.execute_statement(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl_name} ({col_name})")
            except Exception as e:
                logger.debug(f"Index creation notice for {idx_name}: {e}")

    def run_ingestion(self) -> Dict[str, Any]:
        """Executes high-speed batch ETL pipeline for all datasets."""
        start_total = time.time()
        results = []

        console.print("[bold cyan]🚀 Starting PySQL-Sync High-Performance Batch Ingestion...[/bold cyan]")
        console.print(f"[dim]Database Engine: {db.db_type.upper()} | Batch Chunk Size: {self.chunk_size}[/dim]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[green]Ingesting tables...", total=len(config.CSV_FILES))

            for csv_file, table_name in config.CSV_FILES:
                file_path = self.data_dir / csv_file
                if not file_path.exists():
                    console.print(f"[yellow]⚠️ File {csv_file} not found. Skipping.[/yellow]")
                    progress.advance(task)
                    continue

                start_table = time.time()
                
                # Extract & Clean
                df = pd.read_csv(file_path, low_memory=False)
                df = self.clean_dataframe(df, table_name)
                row_count = len(df)

                # Batch Load into DB using SQLAlchemy to_sql
                df.to_sql(
                    name=table_name,
                    con=db.engine,
                    if_exists="replace",
                    index=False,
                    chunksize=self.chunk_size,
                    method="multi" if db.db_type == "mysql" else None,
                )

                elapsed_table = time.time() - start_table
                results.append({
                    "Table": table_name,
                    "Source File": csv_file,
                    "Rows Loaded": f"{row_count:,}",
                    "Columns": len(df.columns),
                    "Time (s)": f"{elapsed_table:.2f}s",
                    "Speed (rows/s)": f"{int(row_count / max(elapsed_table, 0.001)):,}",
                })
                progress.advance(task)

        # Create Indexes after loading
        self.create_indexes()

        total_elapsed = time.time() - start_total

        # Print summary table
        summary_table = Table(title="📊 Ingestion Benchmark & Summary Report", header_style="bold magenta")
        summary_table.add_column("Table", style="cyan")
        summary_table.add_column("Source File", style="white")
        summary_table.add_column("Rows Loaded", justify="right", style="green")
        summary_table.add_column("Columns", justify="right")
        summary_table.add_column("Time", justify="right", style="yellow")
        summary_table.add_column("Ingestion Speed", justify="right", style="bold green")

        for res in results:
            summary_table.add_row(
                res["Table"],
                res["Source File"],
                res["Rows Loaded"],
                str(res["Columns"]),
                res["Time (s)"],
                f"{res['Speed (rows/s)']} r/s",
            )

        console.print(summary_table)
        console.print(f"\n[bold green]✅ ETL Pipeline completed successfully in {total_elapsed:.2f} seconds![/bold green]\n")

        return {
            "total_time": total_elapsed,
            "tables": results,
            "db_type": db.db_type,
        }

    def get_database_stats(self) -> List[Dict[str, Any]]:
        """Returns row count and structure of all tables in the database."""
        stats = []
        for _, table_name in config.CSV_FILES:
            try:
                res = db.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
                count = int(res.iloc[0]["count"])
                stats.append({"table": table_name, "count": count})
            except Exception:
                stats.append({"table": table_name, "count": 0})
        return stats

etl_pipeline = ETLPipeline()
