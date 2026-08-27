import logging
from typing import Dict, Any, List
import pandas as pd
from src.db import db

logger = logging.getLogger(__name__)

# Coordinates mapping for Brazilian states (Center Lat/Lng)
STATE_COORDINATES = {
    "SP": {"lat": -23.5505, "lng": -46.6333, "name": "São Paulo"},
    "RJ": {"lat": -22.9068, "lng": -43.1729, "name": "Rio de Janeiro"},
    "MG": {"lat": -19.9167, "lng": -43.9345, "name": "Minas Gerais"},
    "RS": {"lat": -30.0346, "lng": -51.2177, "name": "Rio Grande do Sul"},
    "PR": {"lat": -25.4284, "lng": -49.2733, "name": "Paraná"},
    "BA": {"lat": -12.9714, "lng": -38.5014, "name": "Bahia"},
    "SC": {"lat": -27.5954, "lng": -48.5480, "name": "Santa Catarina"},
    "GO": {"lat": -16.6869, "lng": -49.2648, "name": "Goiás"},
    "DF": {"lat": -15.7975, "lng": -47.8919, "name": "Distrito Federal"},
    "ES": {"lat": -20.3155, "lng": -40.3128, "name": "Espírito Santo"},
    "PE": {"lat": -8.0476, "lng": -34.8770, "name": "Pernambuco"},
    "CE": {"lat": -3.7319, "lng": -38.5267, "name": "Ceará"},
    "PA": {"lat": -1.4558, "lng": -48.4902, "name": "Pará"},
    "MT": {"lat": -15.6014, "lng": -56.0979, "name": "Mato Grosso"},
    "MA": {"lat": -2.5307, "lng": -44.3068, "name": "Maranhão"},
    "MS": {"lat": -20.4697, "lng": -54.6201, "name": "Mato Grosso do Sul"},
    "PB": {"lat": -7.1195, "lng": -34.8450, "name": "Paraíba"},
    "RN": {"lat": -5.7945, "lng": -35.2110, "name": "Rio Grande do Norte"},
    "PI": {"lat": -5.0920, "lng": -42.8038, "name": "Piauí"},
    "AL": {"lat": -9.6498, "lng": -35.7089, "name": "Alagoas"},
    "SE": {"lat": -10.9472, "lng": -37.0731, "name": "Sergipe"},
    "TO": {"lat": -10.1753, "lng": -48.3311, "name": "Tocantins"},
    "RO": {"lat": -8.7619, "lng": -63.9039, "name": "Rondônia"},
    "AM": {"lat": -3.1190, "lng": -60.0217, "name": "Amazonas"},
    "AC": {"lat": -9.9753, "lng": -67.8249, "name": "Acre"},
    "AP": {"lat": 0.0356, "lng": -51.0705, "name": "Amapá"},
    "RR": {"lat": 2.8235, "lng": -60.6758, "name": "Roraima"},
}

class GeospatialService:
    def __init__(self):
        self.db = db

    def get_state_sales_density(self) -> List[Dict[str, Any]]:
        """Calculates revenue, orders, and customer density by Brazilian state."""
        try:
            query = """
            SELECT 
                c.customer_state,
                COUNT(DISTINCT c.customer_unique_id) AS customer_count,
                COUNT(DISTINCT o.order_id) AS total_orders,
                ROUND(SUM(p.payment_value), 2) AS total_revenue
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN payments p ON o.order_id = p.order_id
            GROUP BY c.customer_state
            ORDER BY total_revenue DESC;
            """
            df = self.db.execute_query(query)
            
            density_data = []
            max_rev = df["total_revenue"].max() if not df.empty else 1.0

            for _, row in df.iterrows():
                state_code = str(row["customer_state"]).upper()
                coords = STATE_COORDINATES.get(state_code, {"lat": -14.235, "lng": -51.925, "name": state_code})
                rev = float(row["total_revenue"] or 0.0)
                
                density_data.append({
                    "state": state_code,
                    "state_name": coords["name"],
                    "lat": coords["lat"],
                    "lng": coords["lng"],
                    "customers": int(row["customer_count"]),
                    "orders": int(row["total_orders"]),
                    "revenue": rev,
                    "intensity": round(rev / max_rev, 3),  # Normalized 0.0 - 1.0 for heatmap
                })
            
            return density_data
        except Exception as e:
            logger.error(f"Error fetching geo density: {e}")
            return []

    def get_top_logistics_routes(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Calculates highest volume shipping routes between sellers and customers."""
        try:
            query = f"""
            SELECT 
                s.seller_state AS origin,
                c.customer_state AS destination,
                COUNT(oi.order_item_id) AS items_shipped,
                ROUND(SUM(oi.price), 2) AS route_value
            FROM order_items oi
            JOIN sellers s ON oi.seller_id = s.seller_id
            JOIN orders o ON oi.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE s.seller_state != c.customer_state
            GROUP BY origin, destination
            ORDER BY items_shipped DESC
            LIMIT {limit};
            """
            df = self.db.execute_query(query)
            routes = []
            for _, row in df.iterrows():
                orig = str(row["origin"]).upper()
                dest = str(row["destination"]).upper()
                orig_coord = STATE_COORDINATES.get(orig)
                dest_coord = STATE_COORDINATES.get(dest)
                if orig_coord and dest_coord:
                    routes.append({
                        "origin": orig,
                        "origin_name": orig_coord["name"],
                        "origin_lat": orig_coord["lat"],
                        "origin_lng": orig_coord["lng"],
                        "destination": dest,
                        "destination_name": dest_coord["name"],
                        "destination_lat": dest_coord["lat"],
                        "destination_lng": dest_coord["lng"],
                        "items_shipped": int(row["items_shipped"]),
                        "route_value": float(row["route_value"]),
                    })
            return routes
        except Exception as e:
            logger.error(f"Error computing routes: {e}")
            return []

geo_service = GeospatialService()
