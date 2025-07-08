import pytest
from unittest.mock import Mock
import requests
from card_fetcher import get_top_commander_cards, get_currency_rates, get_card_prices

# Mock data for EDHREC
EDHREC_HTML_SUCCESS = '''
<html>
    <body>
        <div class="card-grid-item">
            <a class="card-grid-item-card">Sol Ring</a>
        </div>
        <div class="card-grid-item">
            <a class="card-grid-item-card">Arcane Signet</a>
        </div>
    </body>
</html>
'''

# Mock data for Frankfurter.app
CURRENCY_JSON_SUCCESS = {
    "amount": 1.0,
    "base": "EUR",
    "date": "2023-11-10",
    "rates": {
        "CLP": 950.0,
        "USD": 1.07
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

def test_get_top_commander_cards_success(mocker):
    """Test successful scraping of card names from EDHREC."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = EDHREC_HTML_SUCCESS.encode('utf-8')
    mocker.patch('requests.get', return_value=mock_response)
    
    cards = get_top_commander_cards(2)
    assert cards == ["Sol Ring", "Arcane Signet"]

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
    assert eur_to_clp == 950.0
    assert usd_to_clp == pytest.approx((1 / 1.07) * 950.0)

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
