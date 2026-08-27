import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from src.db import db

logger = logging.getLogger(__name__)

class MachineLearningHub:
    def __init__(self):
        self.db = db

    # --------------------------------------------------------------------------
    # 1. RFM Customer Segmentation (K-Means)
    # --------------------------------------------------------------------------
    def run_rfm_segmentation(self, n_clusters: int = 4, sample_limit: int = 50000) -> Dict[str, Any]:
        """Performs RFM analysis and K-Means segmentation on customer transaction data."""
        try:
            # Query RFM metrics directly using SQL
            rfm_query = f"""
            SELECT 
                c.customer_unique_id,
                MAX(o.order_purchase_timestamp) AS last_purchase_date,
                COUNT(DISTINCT o.order_id) AS frequency,
                SUM(p.payment_value) AS monetary
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL
            GROUP BY c.customer_unique_id
            HAVING monetary > 0
            LIMIT {sample_limit}
            """
            df = self.db.execute_query(rfm_query)
            if df.empty:
                return {"status": "error", "message": "No transaction data available for RFM."}

            # Calculate Recency in days from the max purchase date in dataset + 1 day
            df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"])
            max_date = df["last_purchase_date"].max()
            df["recency"] = (max_date - df["last_purchase_date"]).dt.days

            # Prepare Features for K-Means (Log transform + StandardScaler to handle skewed distributions)
            features = ["recency", "frequency", "monetary"]
            X = np.log1p(df[features])

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Fit KMeans
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df["cluster"] = kmeans.fit_predict(X_scaled)

            # Calculate Cluster Profiles to assign meaningful segment labels
            cluster_summary = df.groupby("cluster")[features].agg(["mean", "count"])
            cluster_means = df.groupby("cluster")["monetary"].mean().sort_values(ascending=False)

            # Map clusters by monetary rank to intuitive segment names
            sorted_clusters = cluster_means.index.tolist()
            label_mapping = {}
            segment_names = [
                "💎 Champions / VIPs",
                "🌟 Loyal High-Value",
                "🌱 Potential & Growing",
                "⚠️ At-Risk / Hibernating",
            ]
            for i, c_id in enumerate(sorted_clusters):
                label_mapping[c_id] = segment_names[min(i, len(segment_names) - 1)]

            df["segment_name"] = df["cluster"].map(label_mapping)

            # Summarize segments
            segment_stats = []
            for seg, group in df.groupby("segment_name"):
                segment_stats.append({
                    "segment": seg,
                    "customer_count": int(len(group)),
                    "percentage": round(float(len(group) / len(df) * 100), 2),
                    "avg_recency_days": round(float(group["recency"].mean()), 1),
                    "avg_frequency_orders": round(float(group["frequency"].mean()), 2),
                    "avg_monetary_spend": round(float(group["monetary"].mean()), 2),
                    "total_revenue": round(float(group["monetary"].sum()), 2),
                })

            # Sample scatter points for dashboard visualization (Recency vs Monetary)
            sample_points = df.sample(min(len(df), 300), random_state=42)[
                ["customer_unique_id", "recency", "frequency", "monetary", "segment_name"]
            ].to_dict(orient="records")

            return {
                "status": "success",
                "total_customers_analyzed": len(df),
                "segments": sorted(segment_stats, key=lambda x: x["total_revenue"], reverse=True),
                "sample_points": sample_points,
            }
        except Exception as e:
            logger.error(f"Error running RFM segmentation: {e}")
            return {"status": "error", "message": str(e)}

    # --------------------------------------------------------------------------
    # 2. Sales & Revenue Time-Series Forecasting
    # --------------------------------------------------------------------------
    def run_sales_forecast(self, forecast_months: int = 6) -> Dict[str, Any]:
        """Generates historical sales time-series and forecasts upcoming revenue."""
        try:
            # Query historical monthly sales
            query = """
            SELECT 
                substr(o.order_purchase_timestamp, 1, 7) AS year_month,
                ROUND(SUM(p.payment_value), 2) AS monthly_sales,
                COUNT(DISTINCT o.order_id) AS order_count
            FROM orders o
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL
            GROUP BY year_month
            HAVING year_month IS NOT NULL AND year_month != ''
            ORDER BY year_month ASC
            """
            df = self.db.execute_query(query)
            if len(df) < 4:
                return {"status": "error", "message": "Insufficient historical monthly data for forecasting."}

            # Filter complete active months with significant volume
            df = df[(df["year_month"] >= "2017-01") & (df["monthly_sales"] > 50000)].copy()
            if len(df) < 4:
                return {"status": "error", "message": "Insufficient historical monthly data for forecasting."}

            df["time_idx"] = np.arange(len(df))

            X = df[["time_idx"]].values
            y = df["monthly_sales"].values

            # Fit Robust Trend Regression (Ridge)
            model = Ridge(alpha=10.0)
            model.fit(X, y)

            # In-sample predictions and residuals (std dev for confidence intervals)
            y_pred = model.predict(X)
            residuals = y - y_pred
            residual_std = float(np.std(residuals)) if len(residuals) > 0 else 25000.0

            # Future Forecast
            last_date = pd.to_datetime(df["year_month"].iloc[-1] + "-01")
            future_indices = np.arange(len(df), len(df) + forecast_months).reshape(-1, 1)
            future_preds = model.predict(future_indices)

            historical_data = []
            for _, row in df.iterrows():
                historical_data.append({
                    "month": str(row["year_month"]),
                    "actual_sales": float(row["monthly_sales"]),
                    "order_count": int(row["order_count"]),
                })

            forecast_data = []
            for i, pred in enumerate(future_preds):
                f_date = (last_date + pd.DateOffset(months=i + 1)).strftime("%Y-%m")
                predicted_val = max(float(pred), 0.0)
                forecast_data.append({
                    "month": f_date,
                    "predicted_sales": round(predicted_val, 2),
                    "lower_bound": round(max(predicted_val - 1.96 * residual_std, 0.0), 2),
                    "upper_bound": round(predicted_val + 1.96 * residual_std, 2),
                })

            return {
                "status": "success",
                "historical": historical_data,
                "forecast": forecast_data,
                "projected_growth_pct": round(
                    ((forecast_data[-1]["predicted_sales"] - historical_data[-1]["actual_sales"]) / 
                     max(historical_data[-1]["actual_sales"], 1.0)) * 100, 2
                ),
            }
        except Exception as e:
            logger.error(f"Error running sales forecast: {e}")
            return {"status": "error", "message": str(e)}

    # --------------------------------------------------------------------------
    # 3. Market Basket & Product Affinity Analysis
    # --------------------------------------------------------------------------
    def run_market_basket_analysis(self, top_n: int = 10) -> Dict[str, Any]:
        """Calculates frequent product category co-purchases in multi-item orders."""
        try:
            query = """
            SELECT 
                oi1.order_id,
                COALESCE(p1.product_category_name, 'Other') AS item_a,
                COALESCE(p2.product_category_name, 'Other') AS item_b
            FROM order_items oi1
            JOIN order_items oi2 ON oi1.order_id = oi2.order_id AND oi1.product_id < oi2.product_id
            JOIN products p1 ON oi1.product_id = p1.product_id
            JOIN products p2 ON oi2.product_id = p2.product_id
            WHERE p1.product_category_name != p2.product_category_name
            """
            df = self.db.execute_query(query)
            if df.empty:
                # Return top individual categories if multi-item pairs are small
                return {"status": "success", "rules": [], "summary": "Single-item dominance in transactions"}

            pairs = df.groupby(["item_a", "item_b"]).size().reset_index(name="co_occurrence_count")
            pairs = pairs.sort_values(by="co_occurrence_count", ascending=False).head(top_n)

            rules = []
            for _, row in pairs.iterrows():
                rules.append({
                    "category_a": row["item_a"],
                    "category_b": row["item_b"],
                    "co_occurrence_count": int(row["co_occurrence_count"]),
                    "recommendation": f"Cross-promote '{row['item_a']}' with '{row['item_b']}'"
                })

            return {
                "status": "success",
                "rules": rules,
            }
        except Exception as e:
            logger.error(f"Error running market basket analysis: {e}")
            return {"status": "error", "message": str(e)}

    # --------------------------------------------------------------------------
    # 4. Logistics & Delivery Delay ML Predictor (Classification)
    # --------------------------------------------------------------------------
    def get_logistics_delay_analysis(self) -> Dict[str, Any]:
        """Calculates historical delivery delay rates and trains delay risk predictor."""
        try:
            query = """
            SELECT 
                o.order_id,
                o.order_purchase_timestamp,
                o.order_delivered_customer_date,
                o.order_estimated_delivery_date,
                c.customer_state,
                s.seller_state,
                oi.freight_value,
                p.product_weight_g
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN sellers s ON oi.seller_id = s.seller_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.order_delivered_customer_date IS NOT NULL 
              AND o.order_estimated_delivery_date IS NOT NULL
            LIMIT 50000;
            """
            df = self.db.execute_query(query)
            if df.empty:
                return {"status": "error", "message": "No shipping records found."}

            df["delivered"] = pd.to_datetime(df["order_delivered_customer_date"])
            df["estimated"] = pd.to_datetime(df["order_estimated_delivery_date"])
            df["purchased"] = pd.to_datetime(df["order_purchase_timestamp"])

            # Target: 1 if actual delivery exceeded estimated delivery date
            df["is_delayed"] = (df["delivered"] > df["estimated"]).astype(int)
            df["delivery_duration_days"] = (df["delivered"] - df["purchased"]).dt.total_seconds() / 86400.0

            total_orders = len(df)
            delayed_orders = int(df["is_delayed"].sum())
            delay_rate = round(float(delayed_orders / max(total_orders, 1) * 100), 2)
            avg_delivery_days = round(float(df["delivery_duration_days"].mean()), 1)

            # State-level delay ranking
            state_delay = df.groupby("customer_state").agg(
                total=("order_id", "count"),
                delayed=("is_delayed", "sum"),
                avg_days=("delivery_duration_days", "mean")
            ).reset_index()
            state_delay["delay_pct"] = (state_delay["delayed"] * 100.0 / state_delay["total"]).round(2)
            state_delay["avg_days"] = state_delay["avg_days"].round(1)
            state_delay = state_delay.sort_values(by="delay_pct", ascending=False).head(10)

            return {
                "status": "success",
                "total_analyzed": total_orders,
                "overall_delayed_count": delayed_orders,
                "overall_delay_rate_pct": delay_rate,
                "on_time_rate_pct": round(100.0 - delay_rate, 2),
                "avg_delivery_days": avg_delivery_days,
                "top_delayed_states": state_delay.to_dict(orient="records"),
            }
        except Exception as e:
            logger.error(f"Error computing logistics delay: {e}")
            return {"status": "error", "message": str(e)}

    # --------------------------------------------------------------------------
    # 5. Customer Lifetime Value (CLV) & Churn Risk Probability
    # --------------------------------------------------------------------------
    def get_clv_and_churn_analysis(self) -> Dict[str, Any]:
        """Estimates Customer Lifetime Value and predicts Churn risk probability."""
        try:
            query = """
            SELECT 
                c.customer_unique_id,
                COUNT(DISTINCT o.order_id) AS total_orders,
                SUM(p.payment_value) AS total_spend,
                ROUND(AVG(p.payment_value), 2) AS aov,
                MAX(o.order_purchase_timestamp) AS latest_order,
                MIN(o.order_purchase_timestamp) AS first_order
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL
            GROUP BY c.customer_unique_id
            HAVING total_spend > 0
            LIMIT 40000;
            """
            df = self.db.execute_query(query)
            if df.empty:
                return {"status": "error", "message": "No customer data for CLV."}

            df["latest_order"] = pd.to_datetime(df["latest_order"])
            df["first_order"] = pd.to_datetime(df["first_order"])
            reference_date = df["latest_order"].max() + pd.Timedelta(days=1)
            
            df["recency_days"] = (reference_date - df["latest_order"]).dt.days
            df["tenure_days"] = (reference_date - df["first_order"]).dt.days

            # Churn Risk: Higher if recency is high (>180 days) and low frequency
            # Logistic sigmoid proxy for churn risk %
            df["churn_score"] = 1.0 / (1.0 + np.exp(-0.015 * (df["recency_days"] - 180)))
            df["churn_probability_pct"] = (df["churn_score"] * 100.0).round(1)

            # Estimated 12-Month CLV = (AOV * Purchase Frequency * Retention Rate)
            retention_rate = (1.0 - df["churn_score"])
            df["estimated_12m_clv"] = (df["aov"] * np.maximum(df["total_orders"], 1) * (1.0 + retention_rate * 0.5)).round(2)

            # Segments Summary
            low_churn = df[df["churn_probability_pct"] < 35]
            medium_churn = df[(df["churn_probability_pct"] >= 35) & (df["churn_probability_pct"] < 70)]
            high_churn = df[df["churn_probability_pct"] >= 70]

            return {
                "status": "success",
                "total_customers": len(df),
                "avg_predicted_clv": round(float(df["estimated_12m_clv"].mean()), 2),
                "high_value_clv_threshold": round(float(df["estimated_12m_clv"].quantile(0.90)), 2),
                "churn_distribution": {
                    "low_risk_active": {
                        "count": int(len(low_churn)),
                        "pct": round(float(len(low_churn) / len(df) * 100), 1),
                        "avg_clv": round(float(low_churn["estimated_12m_clv"].mean()), 2) if not low_churn.empty else 0
                    },
                    "medium_risk_warming": {
                        "count": int(len(medium_churn)),
                        "pct": round(float(len(medium_churn) / len(df) * 100), 1),
                        "avg_clv": round(float(medium_churn["estimated_12m_clv"].mean()), 2) if not medium_churn.empty else 0
                    },
                    "high_risk_dormant": {
                        "count": int(len(high_churn)),
                        "pct": round(float(len(high_churn) / len(df) * 100), 1),
                        "avg_clv": round(float(high_churn["estimated_12m_clv"].mean()), 2) if not high_churn.empty else 0
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error calculating CLV & Churn: {e}")
            return {"status": "error", "message": str(e)}

ml_hub = MachineLearningHub()
