import pytest
from src.ai_assistant import ai_assistant

def test_hinglish_lowest_months_2018():
    res = ai_assistant.process_query("brother 2018 mein aise konse 3 mahine hai jinmein sabse kamm profit hua")
    assert res["status"] == "success"
    assert "2018" in res["generated_sql"]
    assert "LIMIT 3" in res["generated_sql"]
    assert "ASC" in res["generated_sql"]
    assert len(res["data"]) == 3

def test_hinglish_top_cities():
    res = ai_assistant.process_query("bhai top 10 jagah bta jaha sbase acha profit hua")
    assert res["status"] == "success"
    assert "customer_city" in res["generated_sql"]
    assert "LIMIT 10" in res["generated_sql"]
    assert len(res["data"]) == 10

def test_hinglish_top_categories():
    res = ai_assistant.process_query("kaunsi category sabse zyada biki")
    assert res["status"] == "success"
    assert "product_category_name" in res["generated_sql"]

def test_hinglish_vip_customers():
    res = ai_assistant.process_query("top 5 log jinhone sabse zyada kharcha kiya")
    assert res["status"] == "success"
    assert "customer_unique_id" in res["generated_sql"]
    assert "LIMIT 5" in res["generated_sql"]
    assert len(res["data"]) == 5

def test_out_of_scope_handling():
    res = ai_assistant.process_query("bhai aaj ka mausam aur cricket score batao")
    assert res["status"] == "out_of_scope"
    assert "uplabdh nahi hai" in res["explanation"] or "database" in res["explanation"]
