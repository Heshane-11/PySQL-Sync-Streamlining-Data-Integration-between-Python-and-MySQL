import pytest
from src.ml_models import ml_hub

def test_ml_hub_instantiation():
    assert ml_hub is not None
