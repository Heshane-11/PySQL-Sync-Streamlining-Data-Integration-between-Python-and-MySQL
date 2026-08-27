import sys
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from rich.console import Console
from rich.table import Table

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.db import db

logger = logging.getLogger(__name__)
console = Console(force_terminal=True)

import time

class AnalyticsEngine:
    def __init__(self):
        self.db = db
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes in-memory cache

    def _get_cached(self, key: str):
        if key in self._cache:
            val, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return val
        return None

    def _set_cached(self, key: str, val: Any):
        self._cache[key] = (val, time.time())

    def get_kpi_summary(self) -> Dict[str, Any]:
        """Calculates overarching executive e-commerce KPIs with instant in-memory cache."""
        cached = self._get_cached("kpi_summary")
        if cached and cached.get("total_orders", 0) > 0:
            return cached

        try:
            kpi_query = """
            SELECT 
                (SELECT COUNT(DISTINCT order_id) FROM orders) AS total_orders,
                (SELECT COUNT(DISTINCT customer_unique_id) FROM customers) AS total_customers,
                (SELECT COUNT(DISTINCT product_id) FROM products) AS total_products,
                (SELECT COUNT(DISTINCT seller_id) FROM sellers) AS total_sellers,
                (SELECT ROUND(SUM(payment_value), 2) FROM payments) AS total_revenue,
                (SELECT ROUND(AVG(payment_value), 2) FROM payments) AS avg_order_value
            """
            df = self.db.execute_query(kpi_query)
            row = df.iloc[0]
            res = {
                "total_orders": int(row["total_orders"] or 0),
                "total_customers": int(row["total_customers"] or 0),
                "total_products": int(row["total_products"] or 0),
                "total_sellers": int(row["total_sellers"] or 0),
                "total_revenue": float(row["total_revenue"] or 0.0),
                "avg_order_value": float(row["avg_order_value"] or 0.0),
            }
            if res["total_orders"] > 0:
                self._set_cached("kpi_summary", res)
            return res
        except Exception as e:
            logger.error(f"Error computing KPIs: {e}")
            return {
                "total_orders": 0, "total_customers": 0, "total_products": 0,
                "total_sellers": 0, "total_revenue": 0.0, "avg_order_value": 0.0
            }

    # 1. Unique Customer Cities
    def get_unique_cities(self, limit: Optional[int] = 50) -> pd.DataFrame:
        query = f"SELECT DISTINCT customer_city FROM customers ORDER BY customer_city ASC"
        if limit:
            query += f" LIMIT {limit}"
        return self.db.execute_query(query)

    # 2. Orders in 2017
    def get_orders_2017(self) -> int:
        query = """
        SELECT COUNT(order_id) AS orders_count 
        FROM orders 
        WHERE substr(order_purchase_timestamp, 1, 4) = '2017'
        """
        df = self.db.execute_query(query)
        return int(df.iloc[0]["orders_count"])

    # 3. Total Sales Per Category
    def get_sales_per_category(self, limit: int = 15) -> pd.DataFrame:
        query = f"""
        SELECT 
            COALESCE(p.product_category_name, 'Other') AS category,
            ROUND(SUM(oi.price), 2) AS total_sales,
            COUNT(oi.order_id) AS items_sold
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY p.product_category_name
        ORDER BY total_sales DESC
        LIMIT {limit}
        """
        return self.db.execute_query(query)

    # 4. Installment Payment Percentage
    def get_installment_percentage(self) -> float:
        query = """
        SELECT 
            ROUND((COUNT(DISTINCT CASE WHEN payment_installments > 1 THEN order_id END) * 100.0) / 
            NULLIF(COUNT(DISTINCT order_id), 0), 2) AS installment_pct
        FROM payments
        """
        df = self.db.execute_query(query)
        return float(df.iloc[0]["installment_pct"] or 0.0)

    # 5. Customers from each state
    def get_customer_counts_by_state(self, limit: int = 20) -> pd.DataFrame:
        query = f"""
        SELECT 
            customer_state, 
            COUNT(customer_id) AS customer_count
        FROM customers
        GROUP BY customer_state
        ORDER BY customer_count DESC
        LIMIT {limit}
        """
        return self.db.execute_query(query)

    # 6. Orders per month in 2018
    def get_monthly_orders_2018(self) -> pd.DataFrame:
        query = """
        SELECT 
            substr(order_purchase_timestamp, 6, 2) AS month_num,
            COUNT(order_id) AS order_count
        FROM orders
        WHERE substr(order_purchase_timestamp, 1, 4) = '2018'
        GROUP BY month_num
        ORDER BY month_num ASC
        """
        return self.db.execute_query(query)

    # 7. Avg products per order grouped by customer city
    def get_avg_products_per_order_by_city(self, limit: int = 15) -> pd.DataFrame:
        query = f"""
        WITH order_item_counts AS (
            SELECT 
                o.order_id,
                c.customer_city,
                COUNT(oi.order_item_id) AS items_in_order
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id, c.customer_city
        )
        SELECT 
            customer_city,
            ROUND(AVG(items_in_order), 2) AS avg_products_per_order,
            COUNT(order_id) AS total_orders
        FROM order_item_counts
        GROUP BY customer_city
        HAVING COUNT(order_id) >= 10
        ORDER BY avg_products_per_order DESC
        LIMIT {limit}
        """
        return self.db.execute_query(query)

    # 8. Revenue Percentage by Category
    def get_category_revenue_distribution(self, limit: int = 10) -> pd.DataFrame:
        query = f"""
        WITH category_sales AS (
            SELECT 
                COALESCE(p.product_category_name, 'Other') AS category,
                SUM(oi.price) AS cat_revenue
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            GROUP BY p.product_category_name
        ),
        total_rev AS (
            SELECT SUM(cat_revenue) AS total_revenue FROM category_sales
        )
        SELECT 
            cs.category,
            ROUND(cs.cat_revenue, 2) AS category_revenue,
            ROUND((cs.cat_revenue * 100.0) / tr.total_revenue, 2) AS revenue_share_pct
        FROM category_sales cs
        CROSS JOIN total_rev tr
        ORDER BY cs.cat_revenue DESC
        LIMIT {limit}
        """
        return self.db.execute_query(query)

    # 9. Correlation between product price and purchase frequency
    def get_price_volume_correlation(self) -> Dict[str, Any]:
        query = """
        SELECT 
            p.product_id,
            AVG(oi.price) AS avg_price,
            COUNT(oi.order_id) AS purchase_count
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY p.product_id
        """
        df = self.db.execute_query(query)
        if len(df) > 1:
            correlation = float(df["avg_price"].corr(df["purchase_count"]))
        else:
            correlation = 0.0
        return {
            "correlation_score": round(correlation, 4),
            "sample_size": len(df),
            "summary": "Moderate negative correlation (Higher price often associates with lower order frequency)" if correlation < -0.1 else "Weak/Neutral correlation"
        }

    # 10. Total revenue by seller with rankings
    def get_seller_rankings(self, limit: int = 15) -> pd.DataFrame:
        query = f"""
        SELECT 
            s.seller_id,
            COALESCE(s.seller_city, 'N/A') AS seller_city,
            COALESCE(s.seller_state, 'N/A') AS seller_state,
            ROUND(SUM(oi.price), 2) AS total_revenue,
            COUNT(oi.order_item_id) AS total_items_sold,
            DENSE_RANK() OVER (ORDER BY SUM(oi.price) DESC) AS revenue_rank
        FROM sellers s
        JOIN order_items oi ON s.seller_id = oi.seller_id
        GROUP BY s.seller_id, s.seller_city, s.seller_state
        ORDER BY total_revenue DESC
        LIMIT {limit}
        """
        return self.db.execute_query(query)

    # 11. Customer order value moving average (sample view)
    def get_customer_moving_avg(self, limit: int = 20) -> pd.DataFrame:
        query = f"""
        SELECT 
            orders.customer_id, 
            orders.order_purchase_timestamp, 
            payments.payment_value AS payment,
            ROUND(AVG(payments.payment_value) OVER(
                PARTITION BY orders.customer_id 
                ORDER BY orders.order_purchase_timestamp 
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ), 2) AS moving_avg_order_value
        FROM payments 
        JOIN orders ON payments.order_id = orders.order_id
        WHERE orders.order_purchase_timestamp IS NOT NULL
        LIMIT {limit}
        """
        return self.db.execute_query(query)

    # 12. Cumulative monthly sales per year
    def get_cumulative_monthly_sales(self) -> pd.DataFrame:
        query = """
        WITH monthly_sales AS (
            SELECT 
                substr(o.order_purchase_timestamp, 1, 4) AS sale_year,
                substr(o.order_purchase_timestamp, 6, 2) AS sale_month,
                ROUND(SUM(p.payment_value), 2) AS monthly_revenue
            FROM orders o
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL
            GROUP BY sale_year, sale_month
        )
        SELECT 
            sale_year,
            sale_month,
            monthly_revenue,
            ROUND(SUM(monthly_revenue) OVER (
                PARTITION BY sale_year 
                ORDER BY sale_month
            ), 2) AS cumulative_revenue
        FROM monthly_sales
        ORDER BY sale_year, sale_month
        """
        return self.db.execute_query(query)

    # 13. Year-over-Year (YoY) growth rate
    def get_yoy_growth(self) -> pd.DataFrame:
        query = """
        WITH annual_sales AS (
            SELECT 
                substr(o.order_purchase_timestamp, 1, 4) AS order_year,
                ROUND(SUM(p.payment_value), 2) AS total_sales
            FROM orders o
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL
            GROUP BY order_year
        )
        SELECT 
            order_year,
            total_sales,
            LAG(total_sales) OVER (ORDER BY order_year) AS previous_year_sales,
            ROUND(
                ((total_sales - LAG(total_sales) OVER (ORDER BY order_year)) * 100.0) / 
                NULLIF(LAG(total_sales) OVER (ORDER BY order_year), 0), 2
            ) AS yoy_growth_percentage
        FROM annual_sales
        WHERE order_year IS NOT NULL AND order_year != ''
        ORDER BY order_year
        """
        return self.db.execute_query(query)

    # 14. Top 3 Customers by spend per year
    def get_top_spending_customers(self) -> pd.DataFrame:
        query = """
        WITH customer_yearly_spend AS (
            SELECT 
                substr(o.order_purchase_timestamp, 1, 4) AS spend_year,
                c.customer_unique_id,
                ROUND(SUM(p.payment_value), 2) AS total_spent,
                DENSE_RANK() OVER (
                    PARTITION BY substr(o.order_purchase_timestamp, 1, 4) 
                    ORDER BY SUM(p.payment_value) DESC
                ) AS rank_in_year
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL AND substr(o.order_purchase_timestamp, 1, 4) != ''
            GROUP BY spend_year, c.customer_unique_id
        )
        SELECT 
            spend_year,
            customer_unique_id,
            total_spent,
            rank_in_year
        FROM customer_yearly_spend
        WHERE rank_in_year <= 3
        ORDER BY spend_year, rank_in_year
        """
        return self.db.execute_query(query)

    def print_analytics_report(self):
        """Displays formatted analytics summary table in console."""
        kpis = self.get_kpi_summary()
        
        console.print("\n[bold cyan]📈 PySQL-Sync Executive KPI Dashboard Summary[/bold cyan]")
        kpi_table = Table(header_style="bold green")
        kpi_table.add_column("Metric", style="cyan")
        kpi_table.add_column("Value", style="bold white", justify="right")
        
        kpi_table.add_row("Total Revenue", f"${kpis['total_revenue']:,.2f}")
        kpi_table.add_row("Total Orders", f"{kpis['total_orders']:,}")
        kpi_table.add_row("Average Order Value (AOV)", f"${kpis['avg_order_value']:.2f}")
        kpi_table.add_row("Total Customers", f"{kpis['total_customers']:,}")
        kpi_table.add_row("Total Products", f"{kpis['total_products']:,}")
        kpi_table.add_row("Total Sellers", f"{kpis['total_sellers']:,}")
        console.print(kpi_table)

        # YoY Growth
        console.print("\n[bold magenta]📅 Year-over-Year (YoY) Sales Growth[/bold magenta]")
        yoy_df = self.get_yoy_growth()
        yoy_table = Table(header_style="bold magenta")
        for col in yoy_df.columns:
            yoy_table.add_column(col.replace("_", " ").title(), justify="right" if "sales" in col or "year" in col or "pct" in col else "left")
        for _, row in yoy_df.iterrows():
            yoy_table.add_row(*[str(val if pd.notnull(val) else "N/A") for val in row])
        console.print(yoy_table)

analytics_engine = AnalyticsEngine()
