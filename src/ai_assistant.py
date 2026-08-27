import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
import pandas as pd

from src.db import db

logger = logging.getLogger(__name__)

# Complete Schema Metadata Context for RAG
DATABASE_SCHEMA_CONTEXT = """
Database Schema & Entity-Relationship Context:
1. customers (customer_id VARCHAR, customer_unique_id VARCHAR, customer_zip_code_prefix INT, customer_city VARCHAR, customer_state VARCHAR)
2. orders (order_id VARCHAR, customer_id VARCHAR, order_status VARCHAR, order_purchase_timestamp DATETIME, order_approved_at DATETIME, order_delivered_carrier_date DATETIME, order_delivered_customer_date DATETIME, order_estimated_delivery_date DATETIME)
3. order_items (order_id VARCHAR, order_item_id INT, product_id VARCHAR, seller_id VARCHAR, shipping_limit_date DATETIME, price FLOAT, freight_value FLOAT)
4. products (product_id VARCHAR, product_category_name VARCHAR, product_name_length INT, product_description_length INT, product_photos_qty INT, product_weight_g FLOAT, product_length_cm FLOAT, product_height_cm FLOAT, product_width_cm FLOAT)
5. payments (order_id VARCHAR, payment_sequential INT, payment_type VARCHAR, payment_installments INT, payment_value FLOAT)
6. sellers (seller_id VARCHAR, seller_zip_code_prefix INT, seller_city VARCHAR, seller_state VARCHAR)
7. geolocation (geolocation_zip_code_prefix INT, geolocation_lat FLOAT, geolocation_lng FLOAT, geolocation_city VARCHAR, geolocation_state VARCHAR)

Key Relationships:
- orders.customer_id = customers.customer_id
- orders.order_id = order_items.order_id
- orders.order_id = payments.order_id
- order_items.product_id = products.product_id
- order_items.seller_id = sellers.seller_id
"""

class UniversalQueryCompiler:
    """
    Dynamic Natural Language to SQL Semantic Compiler.
    Decomposes any user sentence (English / Hindi / Hinglish) into:
    1. Dimension (GROUP BY)
    2. Metrics (SELECT aggregates)
    3. Filters (WHERE clauses)
    4. Sort & Direction (ORDER BY ASC/DESC)
    5. Limit
    6. Dynamic Minimal Join Resolution across schema graph.
    """

    BRAZIL_STATES = {
        "sp": "SP", "sao paulo": "SP", "rj": "RJ", "rio": "RJ", "mg": "MG", "minas": "MG",
        "rs": "RS", "pr": "PR", "sc": "SC", "ba": "BA", "bahia": "BA", "df": "DF", "brasilia": "DF",
        "es": "ES", "go": "GO", "pe": "PE", "ce": "CE", "pa": "PA", "mt": "MT", "ma": "MA",
        "ms": "MS", "pb": "PB", "rn": "RN", "al": "AL", "se": "SE", "to": "TO", "ro": "RO",
        "am": "AM", "ac": "AC", "ap": "AP", "rr": "RR"
    }

    PAYMENT_TYPES = {
        "credit": "credit_card", "credit card": "credit_card", "card": "credit_card",
        "boleto": "boleto", "voucher": "voucher", "debit": "debit_card", "debit card": "debit_card"
    }

    def check_special_domain_cases(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Handles domain-specific boundary questions (e.g. Country, Employee, Inventory)."""
        p = prompt.lower()

        # 1. Country / Desh query (Dataset is strictly Brazil only)
        if any(w in p for w in ["desh", "deshon", "country", "countries", "nation", "nations", "international", "global", "foreign", "world"]):
            return {
                "status": "out_of_scope",
                "user_prompt": prompt,
                "generated_sql": "-- [Dataset Scope Notice]: Single Country Dataset (Brazil Only)",
                "explanation": "⚠️ Is dataset mein sirf ek hi desh (Brazil) ka e-commerce data shamil hai.",
                "insights": [
                    "Yeh database Brazilian E-Commerce operations ka hai, isliye ismein alag-alag deshon (countries) ka data nahi hai.",
                    "💡 **Suggestion:** Aap Brazil ke **States (Rajya)** ya **Cities (Shehar)** ke hisaab se sawaal pooch sakte hain (jaise: *'Sabse kam profit wale states'* ya *'Top 5 revenue cities'*)."
                ],
                "columns": [],
                "data": []
            }

        # 2. Employee / HR / Salary query
        if any(w in p for w in ["employee", "staff", "salary", "tankhwah", "karmchari", "hr", "manager", "ceo", "developer"]):
            return {
                "status": "out_of_scope",
                "user_prompt": prompt,
                "generated_sql": "-- [Out of Scope]: Employee & Salary data is not in E-Commerce DB.",
                "explanation": "⚠️ Employee aur salary ka data is database mein uplabdh nahi hai.",
                "insights": [
                    "Database mein sirf **Customers, Orders, Products, Payments, Sellers, aur Delivery Logistics** ka data hai.",
                    "💡 **Suggestion:** Aap sellers ya customers se related sales aur order volume ke baare mein pooch sakte hain."
                ],
                "columns": [],
                "data": []
            }

        # 3. Inventory / Stock left query
        if any(w in p for w in ["inventory", "warehouse stock", "kitna stock bacha", "godam", "bache hue product"]):
            return {
                "status": "out_of_scope",
                "user_prompt": prompt,
                "generated_sql": "-- [Out of Scope]: Real-time warehouse inventory levels not tracked.",
                "explanation": "⚠️ Live warehouse inventory ya remaining stock ka data uplabdh nahi hai.",
                "insights": [
                    "Database transaction-level sales data track karta hai (kitne items biko aur kis category mein).",
                    "💡 **Suggestion:** Aap *'Top selling categories'* ya *'Konsa product sabse zyada bika'* pooch sakte hain."
                ],
                "columns": [],
                "data": []
            }

        return None

    def check_out_of_scope(self, prompt: str) -> bool:
        p = prompt.lower()
        out_of_scope_terms = [
            "weather", "mausam", "temperature", "stock", "share", "nifty", "sensex",
            "crypto", "bitcoin", "cricket", "ipl", "score", "match", "movie", "film",
            "actor", "song", "gana", "recipe", "khana", "cook", "politics", "election",
            "modi", "president", "chatgpt", "gemini", "who created", "who are you",
            "tum kaun ho", "tera naam kya"
        ]
        return any(term in p for term in out_of_scope_terms)

    def extract_limit(self, prompt: str, default: int = 10) -> int:
        p = prompt.lower()
        numbers = re.findall(r'\b(\d+)\b', p)
        for n in numbers:
            val = int(n)
            if val not in [2016, 2017, 2018, 2019, 2020] and 1 <= val <= 500:
                return val

        if any(w in p for w in ["sabse pehla", "sabse sasta", "sabse mehenga", "top 1", "single", "highest one", "lowest one"]):
            return 1

        return default

    def extract_filters(self, prompt: str) -> Tuple[List[str], Set[str]]:
        p = prompt.lower()
        conditions = []
        needed_tables = set()

        # Year filter
        for yr in ["2016", "2017", "2018"]:
            if yr in p:
                conditions.append(f"substr(o.order_purchase_timestamp, 1, 4) = '{yr}'")
                needed_tables.add("orders")

        # Specific State filter
        for key, code in self.BRAZIL_STATES.items():
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, p) and len(key) > 2:  # Avoid 2-letter collisions like 'to', 'in'
                conditions.append(f"c.customer_state = '{code}'")
                needed_tables.add("customers")
                break

        # Specific Payment Type filter
        for key, ptype in self.PAYMENT_TYPES.items():
            if key in p and not any(w in p for w in ["method", "tarika", "types", "kaunse payment"]):
                conditions.append(f"p.payment_type = '{ptype}'")
                needed_tables.add("payments")
                break

        # Order Status filter
        if any(w in p for w in ["delivered", "deliver", "pahunch", "completed"]):
            conditions.append("o.order_status = 'delivered'")
            needed_tables.add("orders")
        elif any(w in p for w in ["cancel", "cancelled", "radd"]):
            conditions.append("o.order_status = 'canceled'")
            needed_tables.add("orders")

        return conditions, needed_tables

    def detect_sort_direction(self, prompt: str) -> str:
        p = prompt.lower()
        asc_words = [
            "kam", "kamm", "sabse kam", "sabse kamm", "lowest", "least", "bottom", "worst",
            "slow", "down", "min", "minimum", "sasta", "cheapest", "slowest", "kamai kam"
        ]
        return "ASC" if any(w in p for w in asc_words) else "DESC"

    def compile_query(self, user_prompt: str) -> Tuple[str, str, Dict[str, Any]]:
        p = user_prompt.lower().strip()
        limit = self.extract_limit(p, default=10)
        sort_dir = self.detect_sort_direction(p)
        where_conditions, filter_tables = self.extract_filters(p)

        tables_needed: Set[str] = set(filter_tables)
        tables_needed.add("orders")  # Central base table

        # -------------------------------------------------------------
        # 1. CLASSIFY TARGET DIMENSION (GROUP BY)
        # -------------------------------------------------------------
        is_month = any(w in p for w in ["mahina", "mahine", "month", "months", "monthly", "kis mahine", "konse mahine", "trend"])
        is_year = any(w in p for w in ["saal", "year", "years", "yearly", "annual", "growth", "yoy"]) and not is_month
        is_delay = any(w in p for w in ["delay", "delayed", "delays", "late", "deri", "delivery time", "transit", "pohcha", "slow delivery"])
        is_payment = any(w in p for w in ["payment method", "payment methods", "payment type", "tarika", "kaunsa payment", "installments", "kist", "emi"]) and not any(w in p for w in ["mahina", "city", "state", "shehar"])
        is_state = any(w in p for w in ["state", "states", "rajya", "pradesh"])
        is_city = any(w in p for w in ["jagah", "shehar", "city", "cities", "area", "location", "locations", "place", "sthan", "kaha", "jaha"]) and not is_state
        is_seller = any(w in p for w in ["seller", "sellers", "vendor", "vendors", "merchant", "merchants", "dukaan", "dukaandar", "bechne", "supplier"])
        is_customer = any(w in p for w in ["customer", "customers", "grahak", "user", "users", "buyer", "buyers", "khareeddar", "shopper", "shoppers", "people", "log", "vip"]) and not (is_city or is_state)
        is_product = any(w in p for w in ["product", "products", "category", "categories", "samaan", "cheez", "maal", "item", "items", "sasta", "mehenga", "bika"])

        # Metric flags
        is_freight = any(w in p for w in ["freight", "shipping cost", "delivery fee", "delivery charge", "bhaada"])
        is_orders_only = any(w in p for w in ["kitne order", "total orders", "order count", "order volume", "number of orders"]) and not any(w in p for w in ["profit", "revenue", "sales", "kamai"])
        is_price_only = any(w in p for w in ["price", "sasta", "mehenga", "keemat", "average price", "avg price"])

        # Select & Group By Assembly
        select_clause = ""
        group_clause = ""
        order_clause = ""
        explanation = ""

        # --- A. TIME: MONTH ---
        if is_month:
            tables_needed.add("payments")
            where_conditions.append("o.order_purchase_timestamp IS NOT NULL")
            select_clause = """
                substr(o.order_purchase_timestamp, 1, 7) AS year_month,
                COUNT(DISTINCT o.order_id) AS total_orders,
                ROUND(SUM(p.payment_value), 2) AS total_revenue,
                ROUND(AVG(p.payment_value), 2) AS average_order_value
            """
            group_clause = "GROUP BY year_month HAVING year_month IS NOT NULL AND year_month != ''"
            order_clause = f"ORDER BY total_revenue {sort_dir}"
            explanation = f"Monthly financial performance report ({'lowest' if sort_dir=='ASC' else 'highest'} revenue/volume):"

        # --- B. TIME: YEAR ---
        elif is_year:
            tables_needed.add("payments")
            where_conditions.append("o.order_purchase_timestamp IS NOT NULL")
            select_clause = """
                substr(o.order_purchase_timestamp, 1, 4) AS year,
                COUNT(DISTINCT o.order_id) AS total_orders,
                ROUND(SUM(p.payment_value), 2) AS total_revenue,
                ROUND(AVG(p.payment_value), 2) AS average_order_value
            """
            group_clause = "GROUP BY year HAVING year IS NOT NULL AND year != ''"
            order_clause = f"ORDER BY year ASC"
            explanation = "Annual revenue and order growth trajectory across all operational years:"

        # --- C. LOGISTICS / DELAYS ---
        elif is_delay:
            tables_needed.add("customers")
            where_conditions.append("o.order_delivered_customer_date IS NOT NULL")
            where_conditions.append("o.order_estimated_delivery_date IS NOT NULL")
            select_clause = """
                c.customer_state,
                COUNT(o.order_id) AS total_orders,
                ROUND(AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)), 1) AS avg_delivery_days,
                SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS delayed_orders,
                ROUND(SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(o.order_id), 2) AS delay_rate_pct
            """
            group_clause = "GROUP BY c.customer_state"
            order_clause = f"ORDER BY delay_rate_pct {sort_dir}"
            explanation = f"Delivery transit duration and shipping delay risk percentage by state (Top {limit}):"

        # --- D. PAYMENT TYPE ---
        elif is_payment:
            tables_needed.add("payments")
            select_clause = """
                p.payment_type,
                COUNT(o.order_id) AS total_transactions,
                ROUND(SUM(p.payment_value), 2) AS total_payment_value,
                ROUND(AVG(p.payment_installments), 1) AS avg_installments
            """
            group_clause = "GROUP BY p.payment_type"
            order_clause = f"ORDER BY total_payment_value {sort_dir}"
            explanation = "Payment methods breakdown with gross transaction value and average installment terms:"

        # --- E. GEO: CITY / JAGAH ---
        elif is_city:
            tables_needed.add("customers")
            tables_needed.add("payments")
            where_conditions.append("c.customer_city IS NOT NULL AND c.customer_city != ''")
            if is_orders_only:
                select_clause = """
                    c.customer_city,
                    COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
                    COUNT(DISTINCT o.order_id) AS total_orders
                """
                group_clause = "GROUP BY c.customer_city"
                order_clause = f"ORDER BY total_orders {sort_dir}"
                explanation = f"Top {limit} cities ranked by order volume and customer base:"
            else:
                select_clause = """
                    c.customer_city,
                    COUNT(DISTINCT o.order_id) AS total_orders,
                    ROUND(SUM(p.payment_value), 2) AS total_revenue,
                    ROUND(AVG(p.payment_value), 2) AS avg_order_value
                """
                group_clause = "GROUP BY c.customer_city"
                order_clause = f"ORDER BY total_revenue {sort_dir}"
                explanation = f"Top {limit} cities ranked by total sales revenue ({'lowest' if sort_dir=='ASC' else 'highest'}):"

        # --- F. GEO: STATE / RAJYA ---
        elif is_state:
            tables_needed.add("customers")
            tables_needed.add("payments")
            where_conditions.append("c.customer_state IS NOT NULL AND c.customer_state != ''")
            select_clause = """
                c.customer_state,
                COUNT(DISTINCT o.order_id) AS total_orders,
                ROUND(SUM(p.payment_value), 2) AS total_revenue,
                ROUND(AVG(p.payment_value), 2) AS avg_order_value
            """
            group_clause = "GROUP BY c.customer_state"
            order_clause = f"ORDER BY total_revenue {sort_dir}"
            explanation = f"State-wise gross sales performance (Top {limit} states):"

        # --- G. SELLER ---
        elif is_seller:
            tables_needed.add("order_items")
            tables_needed.add("sellers")
            select_clause = """
                s.seller_id,
                s.seller_city,
                s.seller_state,
                COUNT(oi.order_item_id) AS items_sold,
                ROUND(SUM(oi.price), 2) AS gross_sales
            """
            group_clause = "GROUP BY s.seller_id, s.seller_city, s.seller_state"
            order_clause = f"ORDER BY gross_sales {sort_dir}"
            explanation = f"Top {limit} sellers performance ranking by sales and units sold:"

        # --- H. CUSTOMER / VIP ---
        elif is_customer:
            tables_needed.add("customers")
            tables_needed.add("payments")
            select_clause = """
                c.customer_unique_id,
                c.customer_city,
                c.customer_state,
                COUNT(DISTINCT o.order_id) AS total_orders,
                ROUND(SUM(p.payment_value), 2) AS total_spent
            """
            group_clause = "GROUP BY c.customer_unique_id, c.customer_city, c.customer_state"
            order_clause = f"ORDER BY total_spent {sort_dir}"
            explanation = f"Top {limit} highest spending customers (VIP Ranking):"

        # --- I. PRODUCT CATEGORY & PRICE / FREIGHT ---
        elif is_product or is_freight or is_price_only or any(w in p for w in ["profit", "kamai", "sales", "revenue", "samaan", "item"]):
            tables_needed.add("order_items")
            tables_needed.add("products")
            if is_freight:
                select_clause = """
                    COALESCE(pr.product_category_name, 'Other') AS category,
                    COUNT(oi.order_item_id) AS units_sold,
                    ROUND(AVG(oi.freight_value), 2) AS avg_freight_cost,
                    ROUND(SUM(oi.freight_value), 2) AS total_freight_spend
                """
                group_clause = "GROUP BY pr.product_category_name"
                order_clause = f"ORDER BY total_freight_spend {sort_dir}"
                explanation = f"Product categories ranked by shipping freight expenditure:"
            elif is_price_only:
                select_clause = """
                    COALESCE(pr.product_category_name, 'Other') AS category,
                    COUNT(oi.order_item_id) AS units_sold,
                    ROUND(MIN(oi.price), 2) AS min_price,
                    ROUND(AVG(oi.price), 2) AS avg_price,
                    ROUND(MAX(oi.price), 2) AS max_price
                """
                group_clause = "GROUP BY pr.product_category_name"
                order_clause = f"ORDER BY avg_price {sort_dir}"
                explanation = f"Product categories price analysis ({'cheapest' if sort_dir=='ASC' else 'most expensive'}):"
            else:
                select_clause = """
                    COALESCE(pr.product_category_name, 'Other') AS category,
                    COUNT(oi.order_item_id) AS units_sold,
                    ROUND(SUM(oi.price), 2) AS total_sales,
                    ROUND(AVG(oi.price), 2) AS avg_price
                """
                group_clause = "GROUP BY pr.product_category_name"
                order_clause = f"ORDER BY total_sales {sort_dir}"
                explanation = f"Top {limit} product categories by sales performance:"

        # --- J. SMART DEFAULT FALLBACK ---
        else:
            tables_needed.add("customers")
            tables_needed.add("payments")
            select_clause = """
                c.customer_city,
                COUNT(DISTINCT o.order_id) AS total_orders,
                ROUND(SUM(p.payment_value), 2) AS total_revenue
            """
            group_clause = "GROUP BY c.customer_city"
            order_clause = f"ORDER BY total_revenue DESC"
            explanation = f"Top performing commercial regions ranked by total gross sales:"

        # -------------------------------------------------------------
        # 2. DYNAMIC JOIN RESOLUTION
        # -------------------------------------------------------------
        joins = []
        if "customers" in tables_needed:
            joins.append("JOIN customers c ON o.customer_id = c.customer_id")
        if "payments" in tables_needed:
            joins.append("JOIN payments p ON o.order_id = p.order_id")
        if "order_items" in tables_needed or "products" in tables_needed or "sellers" in tables_needed:
            joins.append("JOIN order_items oi ON o.order_id = oi.order_id")
        if "products" in tables_needed:
            joins.append("JOIN products pr ON oi.product_id = pr.product_id")
        if "sellers" in tables_needed:
            joins.append("JOIN sellers s ON oi.seller_id = s.seller_id")

        join_str = "\n".join(joins)
        where_str = ("WHERE " + " AND ".join(where_conditions)) if where_conditions else ""

        full_sql = f"""
SELECT {select_clause.strip()}
FROM orders o
{join_str}
{where_str}
{group_clause}
{order_clause}
LIMIT {limit};
        """.strip()

        return full_sql, explanation, {"tables": list(tables_needed), "limit": limit}


class SchemaRAGAssistant:
    def __init__(self):
        self.db = db
        self.compiler = UniversalQueryCompiler()

    def retrieve_schema_for_prompt(self, user_prompt: str) -> str:
        """Retrieves relevant table schema and constraints based on keywords in prompt."""
        prompt_lower = user_prompt.lower()
        selected_tables = []
        
        if any(w in prompt_lower for w in ["customer", "city", "state", "user", "buyer", "location", "who", "jagah", "shehar", "rajya"]):
            selected_tables.append("customers")
        if any(w in prompt_lower for w in ["order", "purchase", "bought", "delivered", "date", "status", "year", "month", "mahina"]):
            selected_tables.append("orders")
        if any(w in prompt_lower for w in ["item", "price", "freight", "shipping", "cost", "revenue", "sales", "profit", "kamai"]):
            selected_tables.append("order_items")
        if any(w in prompt_lower for w in ["product", "category", "item", "weight", "samaan", "cheez"]):
            selected_tables.append("products")
        if any(w in prompt_lower for w in ["payment", "installment", "credit", "voucher", "money", "spent", "revenue", "paisa", "kist"]):
            selected_tables.append("payments")
        if any(w in prompt_lower for w in ["seller", "vendor", "merchant", "dukaan", "bechne"]):
            selected_tables.append("sellers")
        if any(w in prompt_lower for w in ["map", "coordinate", "lat", "lng", "geo"]):
            selected_tables.append("geolocation")

        if not selected_tables:
            return DATABASE_SCHEMA_CONTEXT

        schema_lines = [DATABASE_SCHEMA_CONTEXT.split("Key Relationships:")[0]]
        return "\n".join(schema_lines)

    def process_query(self, user_prompt: str) -> Dict[str, Any]:
        """Orchestrates Out-of-Scope check, Dynamic SQL compilation, DB execution, and natural explanations."""
        try:
            # 1. Special Domain Boundary Check (Single Country Brazil, Employee, Inventory)
            special_res = self.compiler.check_special_domain_cases(user_prompt)
            if special_res:
                return special_res

            # 2. General Out-of-Scope Check (Weather, Stocks, Cricket, etc.)
            if self.compiler.check_out_of_scope(user_prompt):
                return {
                    "status": "out_of_scope",
                    "user_prompt": user_prompt,
                    "generated_sql": "-- [Out of Scope]: Query does not match E-Commerce Schema.",
                    "explanation": "⚠️ Yeh jaankari hamare E-Commerce database mein uplabdh nahi hai.",
                    "insights": [
                        "Hamare database mein **Orders, Customers, Products, Payments, Sellers, aur Delivery Logistics** ka data available hai.",
                        "Aap inse related koi bhi sawaal pooch sakte hain (e.g. *'Top 5 revenue cities'*, *'2018 ke sabse kam profit wale 3 mahine'*, *'Konsa product category sabse sasta hai'*, *'Average delivery time per state'*)."
                    ],
                    "columns": [],
                    "data": []
                }

            # 2. Universal SQL Compilation
            sql_query, explanation, meta = self.compiler.compile_query(user_prompt)
            df = self.db.execute_query(sql_query)
            
            if df.empty:
                return {
                    "status": "no_data",
                    "user_prompt": user_prompt,
                    "generated_sql": sql_query.strip(),
                    "explanation": "ℹ️ Is query ke filter criteria ke mutabik database mein koi records nahi mile.",
                    "insights": ["Aap date filter ya search criteria ko thoda broad karke dobara pooch sakte hain."],
                    "columns": [],
                    "data": []
                }

            insights = []
            first_row = df.iloc[0]
            cols = df.columns.tolist()
            val_0 = first_row.iloc[0]
            val_last = first_row.iloc[-1]
            if isinstance(val_last, (int, float)):
                insights.append(f"Rank 1: **{val_0}** ({cols[-1].replace('_', ' ')}: **${val_last:,.2f}**).")
            else:
                insights.append(f"Rank 1: **{val_0}** ({cols[-1].replace('_', ' ')}: **{val_last}**).")
            insights.append(f"Total {len(df)} matching rows retrieved.")

            return {
                "status": "success",
                "user_prompt": user_prompt,
                "generated_sql": sql_query.strip(),
                "explanation": explanation,
                "insights": insights,
                "columns": df.columns.tolist(),
                "data": df.where(pd.notnull(df), None).to_dict(orient="records"),
            }
        except Exception as e:
            logger.error(f"Error processing AI query: {e}")
            return {
                "status": "error",
                "user_prompt": user_prompt,
                "message": f"Failed to compile and execute query: {str(e)}"
            }

ai_assistant = SchemaRAGAssistant()
