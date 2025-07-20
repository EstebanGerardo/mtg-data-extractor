import requests
import logging
import time
from bs4 import BeautifulSoup
import threading
from concurrent.futures import Future
import random

EDHREC_BASE_URL = 'https://edhrec.com/top'
SCRYFALL_API_URL = 'https://api.scryfall.com/cards/named'
CURRENCY_API_URL = 'https://api.exchangerate-api.com/v4/latest/USD'

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]



def get_top_commander_cards_direct(time_period="week", num_cards=100):
    """
    Fetches the top commander cards and their prices from EDHREC for a given time period using direct requests.
    Uses rotating user agents to avoid blocking.
    Returns a list of dictionaries with card names, prices (multiple sources), and deck statistics.
    """
    try:
        logging.info("Fetching top commander cards from EDHREC...")
        
        # Map time periods to EDHREC URL paths
        time_map = {
            "week": "",  # Default is week
            "month": "/month",
            "2years": "/2years",
            "all": "/all"
        }
        
        # Use the appropriate URL based on time period
        url = f"https://edhrec.com/top{time_map.get(time_period, '')}"
        
        logging.info(f"Fetching top commander cards from {url}...")
        
        # Use a random user agent
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all card containers using the CSS class
            card_containers = soup.find_all('div', class_='Card_container__Ng56K')
            logging.info(f"Found {len(card_containers)} card containers")
            
            if not card_containers:
                logging.error("No card containers found with class 'Card_container__Ng56K'")
                raise Exception("Failed to extract card data from EDHREC page - no card containers found")
            
            # Extract card data from HTML elements
            card_data = []
            for i, container in enumerate(card_containers[:num_cards]):
                try:
                    # Extract card name
                    name_element = container.find('span', class_='Card_name__Mpa7S')
                    card_name = name_element.get_text(strip=True) if name_element else f"Unknown Card {i+1}"
                    
                    # Extract deck count info from label
                    label_element = container.find('div', class_='CardLabel_label__iAM7T')
                    deck_count_text = label_element.get_text(strip=True) if label_element else ""
                    
                    # Parse deck count from text like "In 5391523 decks"
                    deck_count = None
                    deck_percentage = None
                    total_decks = None
                    
                    if deck_count_text:
                        try:
                            # Extract number from "In X decks" format
                            import re
                            deck_match = re.search(r'In (\d+) decks', deck_count_text)
                            if deck_match:
                                deck_count = int(deck_match.group(1))
                            
                            # Extract percentage from text like "69: 84% of 6401472 decks"
                            percent_match = re.search(r'(\d+)% of (\d+) decks', deck_count_text)
                            if percent_match:
                                deck_percentage = int(percent_match.group(1))
                                total_decks = int(percent_match.group(2))
                        except (ValueError, AttributeError):
                            pass
                    
                    # Fetch prices from Scryfall API
                    logging.info(f"Fetching prices for {card_name}...")
                    usd_price, eur_price = get_card_prices(card_name)
                    
                    card_info = {
                        'name': card_name,
                        # EDHREC data (extracted from HTML)
                        'edhrec_data': {
                            'deck_count': deck_count,
                            'deck_percentage': deck_percentage,
                            'total_decks': total_decks,
                            'source': 'EDHREC HTML'
                        },
                        # Scryfall price data (from API)
                        'scryfall_prices': {
                            'usd': float(usd_price) if usd_price else None,
                            'eur': float(eur_price) if eur_price else None,
                            'source': 'Scryfall API'
                        },
                        # Legacy format for backward compatibility
                        'deck_count': deck_count,
                        'deck_percentage': deck_percentage,
                        'total_decks': total_decks,
                        'usd_price': float(usd_price) if usd_price else None,
                        'eur_price': float(eur_price) if eur_price else None
                    }
                    
                    card_data.append(card_info)
                    logging.info(f"Extracted card: {card_name}, Deck count: {deck_count}, Percentage: {deck_percentage}%")
                    
                except Exception as e:
                    logging.error(f"Error processing card container {i}: {e}")
                    continue
            
            if not card_data:
                logging.error("Could not extract any card data from page.")
                raise Exception("Failed to extract any card data from EDHREC page")
            
            logging.info(f"Successfully fetched {len(card_data)} cards with price information.")
            return card_data
            
        except Exception as e:
            logging.error(f"Error fetching from EDHREC: {e}")
            raise

    except Exception as e:
        logging.error(f"An error occurred while fetching commander cards: {e}", exc_info=True)
        raise

def get_top_commander_cards(time_period="week", num_cards=100):
    """
    Fetches the top commander cards from EDHREC for a given time period.
    Returns a list of dictionaries with card names and prices.
    """
    try:
        return get_top_commander_cards_direct(time_period, num_cards)
    except Exception as e:
        logging.error(f"Error in get_top_commander_cards: {e}")
        raise

def get_currency_rates():
    """Fetches currency conversion rates for USD and EUR to CLP."""
    try:
        logging.info("Fetching currency rates from exchangerate-api.com")
        response = requests.get(CURRENCY_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        rates = data.get('rates', {})
        
        # The API provides rates from USD to other currencies
        usd_to_clp = rates.get('CLP')
        usd_to_eur = rates.get('EUR')

        if not usd_to_clp or not usd_to_eur:
            logging.error("Could not retrieve all required currency rates from API response.")
            logging.error(f"Available rates: {list(rates.keys())[:10]}...")  # Show first 10 available rates
            return None, None
            
        # To get EUR to CLP, we convert EUR -> USD -> CLP
        eur_to_clp = (1 / usd_to_eur) * usd_to_clp
        logging.info(f"Rates fetched: 1 USD = {usd_to_clp} CLP, 1 EUR = {eur_to_clp:.2f} CLP")
        return usd_to_clp, eur_to_clp
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch currency rates: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Error processing currency rates: {e}")
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
