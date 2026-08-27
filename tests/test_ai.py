import pytest
from src.ai_assistant import ai_assistant

def test_ai_schema_retrieval():
    schema = ai_assistant.retrieve_schema_for_prompt("Which cities have the highest revenue?")
    assert "customers" in schema or "orders" in schema or "payments" in schema

def test_ai_query_generation_and_execution():
    res = ai_assistant.process_query("Top 3 cities by sales")
    assert res["status"] == "success"
    assert "SELECT" in res["generated_sql"].upper()
    assert len(res["data"]) <= 3
