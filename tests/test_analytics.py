import pytest
from src.analytics import analytics_engine

def test_kpi_summary_structure():
    kpis = analytics_engine.get_kpi_summary()
    assert isinstance(kpis, dict)
    assert "total_revenue" in kpis
    assert "total_orders" in kpis
    assert "total_customers" in kpis
    assert "avg_order_value" in kpis
