import pytest
from unittest.mock import Mock
import requests
from card_fetcher import get_top_commander_cards, get_currency_rates, get_card_prices

# Mock data for EDHREC JSON
EDHREC_JSON_SUCCESS = {
    "cardlist": [
        {"name": "Sol Ring"},
        {"name": "Arcane Signet"},
        {"name": "Command Tower"}
    ]
}

# Mock data for Frankfurter.app (USD base)
CURRENCY_JSON_SUCCESS = {
    "amount": 1.0,
    "base": "USD",
    "date": "2023-11-10",
    "rates": {
        "CLP": 930.0,
        "EUR": 0.93
    }
}

# Mock data for Scryfall
SCRYFALL_JSON_SUCCESS = {
    "prices": {
        "usd": "1.50",
        "eur": "1.20"
    }
}

# --- Tests for get_top_commander_cards ---

@pytest.mark.parametrize("num_cards, expected_cards", [
    (3, ["Sol Ring", "Arcane Signet", "Command Tower"]),
    (2, ["Sol Ring", "Arcane Signet"]),
    (1, ["Sol Ring"])
])
def test_get_top_commander_cards_success(mocker, num_cards, expected_cards):
    """Test successful fetching of card names from EDHREC JSON."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = EDHREC_JSON_SUCCESS
    mocker.patch('requests.get', return_value=mock_response)
    
    cards = get_top_commander_cards(num_cards)
    assert cards == expected_cards
    # Specifically check the user's request for N=3
    if num_cards == 3:
        assert len(cards) == 3

def test_get_top_commander_cards_failure(mocker):
    """Test failure in fetching from EDHREC."""
    mocker.patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error"))
    
    cards = get_top_commander_cards(2)
    assert cards == []

# --- Tests for get_currency_rates ---

def test_get_currency_rates_success(mocker):
    """Test successful fetching of currency rates."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = CURRENCY_JSON_SUCCESS
    mocker.patch('requests.get', return_value=mock_response)
    
    usd_to_clp, eur_to_clp = get_currency_rates()
    assert usd_to_clp == 930.0
    assert eur_to_clp == pytest.approx((1 / 0.93) * 930.0)

def test_get_currency_rates_failure(mocker):
    """Test failure in fetching currency rates."""
    mocker.patch('requests.get', side_effect=requests.exceptions.RequestException("API error"))
    
    rates = get_currency_rates()
    assert rates == (None, None)

# --- Tests for get_card_prices ---

def test_get_card_prices_success(mocker):
    """Test successful fetching of card prices from Scryfall."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SCRYFALL_JSON_SUCCESS
    mocker.patch('requests.get', return_value=mock_response)
    
    ck_price, cm_price = get_card_prices("Sol Ring")
    assert ck_price == "1.50"
    assert cm_price == "1.20"

def test_get_card_prices_not_found(mocker):
    """Test handling of a 404 error when a card is not found."""
    mock_response = Mock()
    mock_response.status_code = 404
    mocker.patch('requests.get', return_value=mock_response)
    
    prices = get_card_prices("Nonexistent Card")
    assert prices == (None, None)

def test_get_card_prices_request_failure(mocker):
    """Test failure in fetching card prices due to a request exception."""
    mocker.patch('requests.get', side_effect=requests.exceptions.RequestException("Network error"))
    
    prices = get_card_prices("Sol Ring")
    assert prices == (None, None)
