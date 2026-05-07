import pytest
from unittest.mock import MagicMock, patch
from agents.support_agent import SupportAgent
from agents.forecast_agent import ForecastAgent

# Tests for SupportAgent
def test_support_agent_greeting():
    agent = SupportAgent()
    # No mocks needed for simple greeting
    response = agent.process_query("hi", customer_name="TestUser")
    assert isinstance(response, str)
    assert "TestUser" in response

@patch('agents.support_agent.get_db_connection')
def test_support_agent_availability(mock_get_db):
    # Setup mock DB
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock product found
    mock_product = MagicMock()
    mock_product.name = "Sugar"
    mock_product.stock = 10
    mock_product.unit = "kg"
    mock_cursor.fetchone.return_value = mock_product
    
    agent = SupportAgent()
    response = agent.process_query("is there sugar?")
    assert isinstance(response, str)
    assert "Sugar" in response

# Tests for ForecastAgent
@patch('agents.forecast_agent.get_db_connection')
@patch('agents.forecast_agent.azure_ml_service')
def test_forecast_agent_success(mock_ml, mock_get_db):
    # Setup mock DB
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    mock_product = MagicMock()
    mock_product.name = "Milk"
    mock_product.stock = 50
    mock_product.price = 1.5
    mock_cursor.fetchone.return_value = mock_product
    
    # Setup mock ML
    mock_ml.predict.return_value = [25.5]
    
    agent = ForecastAgent()
    result = agent.predict_product_demand("Milk")
    
    assert isinstance(result, dict)
    expected_keys = ["product_name", "current_stock", "predicted_demand", "is_weekend"]
    for key in expected_keys:
        assert key in result
    assert result["product_name"] == "Milk"

@patch('agents.forecast_agent.get_db_connection')
def test_forecast_agent_not_found(mock_get_db):
    # Setup mock DB to return no product
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    
    agent = ForecastAgent()
    result = agent.predict_product_demand("UnknownItem")
    
    assert isinstance(result, dict)
    assert "error" in result
    assert "not found" in result["error"]
