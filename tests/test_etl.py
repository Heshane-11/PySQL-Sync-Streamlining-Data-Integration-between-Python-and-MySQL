import pytest
import pandas as pd
from src.etl import etl_pipeline

def test_clean_dataframe():
    sample_df = pd.DataFrame({
        "Customer ID": ["c1", "c2"],
        "order-date": ["2018-01-01", "2018-01-02"],
        "product.category": ["electronics", "furniture"]
    })
    cleaned = etl_pipeline.clean_dataframe(sample_df, "products")
    assert "customer_id" in cleaned.columns
    assert "order_date" in cleaned.columns
    assert "product_category_name" in cleaned.columns
