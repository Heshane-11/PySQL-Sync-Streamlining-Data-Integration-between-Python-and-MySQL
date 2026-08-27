import pytest
import pandas as pd
from src.db import db

def test_db_connection():
    connected, msg = db.check_connection()
    assert connected is True, f"Database failed to connect: {msg}"

def test_db_execute_query():
    df = db.execute_query("SELECT 1 AS test_col")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["test_col"] == 1
