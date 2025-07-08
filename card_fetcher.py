import requests
from bs4 import BeautifulSoup
import logging
import time

EDHREC_URL = "https://edhrec.com/top"
SCRYFALL_API_URL = "https://api.scryfall.com/cards/named"
CURRENCY_API_URL = "https://api.frankfurter.app/latest"

def get_top_commander_cards(num_cards: int):
    """Scrapes the EDHREC 'Top Cards' page to get a list of the most popular cards."""
    try:
        logging.info(f"Fetching top {num_cards} cards from EDHREC.")
        response = requests.get(EDHREC_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # The new selector for card names on EDHREC as of recent changes.
        card_items = soup.select('div.Card_name__1H-3c')
        if not card_items:
            logging.error("Could not find card items on EDHREC page.")
            return []
        card_names = [item.text.strip() for item in card_items[:num_cards]]
        logging.info(f"Successfully fetched {len(card_names)} card names.")
        return card_names
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from EDHREC: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred while scraping EDHREC: {e}")
        return []

def get_currency_rates():
    """Fetches currency conversion rates for USD and EUR to CLP."""
    try:
        logging.info("Fetching currency rates from Frankfurter.app")
        response = requests.get(f"{CURRENCY_API_URL}?to=CLP,USD,EUR")
        response.raise_for_status()
        rates = response.json().get('rates', {})
        # We need rates relative to a base currency, e.g., USD to CLP and EUR to CLP.
        # The API gives rates based on EUR by default. Let's get CLP per EUR and CLP per USD.
        eur_to_clp = rates.get('CLP')
        usd_to_eur = rates.get('USD') # This is EUR per 1 USD
        if not eur_to_clp or not usd_to_eur:
            logging.error("Could not retrieve all required currency rates.")
            return None, None
        # To get USD to CLP, we convert USD -> EUR -> CLP
        usd_to_clp = (1 / usd_to_eur) * eur_to_clp
        logging.info(f"Rates fetched: 1 EUR = {eur_to_clp} CLP, 1 USD = {usd_to_clp} CLP")
        return usd_to_clp, eur_to_clp
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch currency rates: {e}")
        return None, None

def get_card_prices(card_name: str):
    """Fetches card prices from Card Kingdom (USD) and Cardmarket (EUR) via the Scryfall API."""
    try:
        logging.info(f"Fetching prices for {card_name} from Scryfall.")
        response = requests.get(SCRYFALL_API_URL, params={'exact': card_name})
        time.sleep(100/1000) # Scryfall API rate limit: 10 requests/second
        if response.status_code == 404:
            logging.warning(f"Card '{card_name}' not found on Scryfall.")
            return None, None
        response.raise_for_status()
        data = response.json()
        prices = data.get('prices', {})
        ck_price_usd = prices.get('usd')
        cm_price_eur = prices.get('eur')
        return ck_price_usd, cm_price_eur
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch price for {card_name}: {e}")
        return None, None
