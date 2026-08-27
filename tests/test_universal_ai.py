import pytest
from src.ai_assistant import ai_assistant

def test_query_lowest_3_months_2018():
    res = ai_assistant.process_query("brother 2018 mein aise konse 3 mahine hai jinmein sabse kamm profit hua")
    assert res["status"] == "success"
    assert len(res["data"]) == 3
    assert res["data"][0]["year_month"].startswith("2018")

def test_query_top_10_cities_revenue():
    res = ai_assistant.process_query("bhai top 10 jagah bta jaha sbase acha profit hua")
    assert res["status"] == "success"
    assert len(res["data"]) == 10
    assert "customer_city" in res["columns"]

def test_query_cheapest_category():
    res = ai_assistant.process_query("konsi category sabse sasti hai")
    assert res["status"] == "success"
    assert "category" in res["columns"] or "product_category_name" in res["columns"]

def test_query_freight_by_category():
    res = ai_assistant.process_query("kaunsi product category mein sabse zyada freight cost hai")
    assert res["status"] == "success"
    assert "freight" in res["generated_sql"]

def test_query_top_sellers():
    res = ai_assistant.process_query("top 5 sellers jinka sales sabse badiya raha")
    assert res["status"] == "success"
    assert len(res["data"]) == 5
    assert "seller_id" in res["columns"]

def test_query_state_delays():
    res = ai_assistant.process_query("sabse zyada delay kis state mein hua")
    assert res["status"] == "success"
    assert "customer_state" in res["columns"]

def test_query_payment_methods():
    res = ai_assistant.process_query("kis payment method se sabse zyada transaction hui")
    assert res["status"] == "success"
    assert "payment_type" in res["columns"]

def test_query_vip_customers():
    res = ai_assistant.process_query("top 5 VIP grahak jinhone sabse zyada paisa kharcha kiya")
    assert res["status"] == "success"
    assert len(res["data"]) == 5
    assert "customer_unique_id" in res["columns"]

def test_query_out_of_scope():
    res = ai_assistant.process_query("bhai kal ka mausam kaisa hoga aur IPL score batao")
    assert res["status"] == "out_of_scope"

def test_query_country_scope_notice():
    res = ai_assistant.process_query("aisa konsa desh h jaha sabse kamm profit hua")
    assert res["status"] == "out_of_scope"
    assert "Brazil" in res["explanation"] or "Brazil" in res["insights"][0]
