import pytest
from src.geo import geo_service

def test_geo_density():
    density = geo_service.get_state_sales_density()
    assert isinstance(density, list)
    assert len(density) > 0
    first = density[0]
    assert "state" in first
    assert "lat" in first
    assert "lng" in first
    assert "revenue" in first

def test_geo_routes():
    routes = geo_service.get_top_logistics_routes(5)
    assert isinstance(routes, list)
