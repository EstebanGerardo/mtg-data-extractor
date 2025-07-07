import json
import logging
import re
import sys
import requests
import time
from bs4 import BeautifulSoup

# --- IMPORTANT ---
# You need a ScraperAPI key for this script to work.
# Sign up for a free account at https://www.scraperapi.com/ to get your key.
API_KEY = "c9cae1f6575ed03003e74f659d1154fa"  # User-provided key

# Setup logging to a file and to stderr for comprehensive diagnostics.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log", mode='w'), # 'w' overwrites the log file on each run
        logging.StreamHandler(sys.stderr)
    ]
)

# --- Constants ---
BASE_URL = "https://www.cardmarket.com"
MAX_SELLERS_TO_CHECK = 50
SCRAPERAPI_URL = "http://api.scraperapi.com"

def get_page_content(url, retries=3, delay=5):
    """Fetches the HTML content of a URL using the ScraperAPI with retries and JS rendering."""
    logging.info(f"Requesting URL via ScraperAPI: {url}")
    params = {
        'api_key': API_KEY,
        'url': url,
        'render': 'true' # Enable JavaScript rendering
    }
    for attempt in range(retries):
        try:
            # Set a 70-second timeout as recommended by ScraperAPI docs
            response = requests.get(SCRAPERAPI_URL, params=params, timeout=70)
            if response.status_code == 200:
                logging.info("Successfully fetched page content.")
                return response.content
            elif 500 <= response.status_code < 600:
                logging.warning(f"ScraperAPI request failed with status code {response.status_code} (attempt {attempt + 1}/{retries}). Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"ScraperAPI request failed with a non-retriable status code {response.status_code}")
                logging.error(f"Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"An exception occurred during the request (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)

    logging.error(f"Failed to fetch URL after {retries} attempts.")
    return None

def find_best_offer(card_name):
    """
    Finds the best offer for a given card by scraping Cardmarket.
    It checks up to MAX_SELLERS_TO_CHECK and saves all analyzed sellers to a JSON file.
    """
    logging.info(f"Starting to find best offer for: {card_name}")

    if not API_KEY or "YOUR_SCRAPERAPI_KEY" in API_KEY:
        error_msg = "Please add your ScraperAPI key to scraper.py"
        logging.error(error_msg)
        return {"error": error_msg}

    sellers_analyzed = []

    try:
        search_query = "+".join(card_name.split())
        search_url = f"{BASE_URL}/en/Magic/Products/Search?searchString={search_query}"
        
        content = get_page_content(search_url)
        if not content:
            return {"error": "Failed to retrieve search results page."}

        soup = BeautifulSoup(content, 'lxml')
        product_link_element = soup.select_one(".table-body .row .col-md-8 a, .table-body .row .col-12 > a")

        if not product_link_element or not product_link_element.has_attr('href'):
            logging.error("Card not found on search page.")
            return {"error": "Card not found. Please check spelling or try a more specific name."}
        
        listings_url = BASE_URL + product_link_element['href']
        content = get_page_content(listings_url)
        if not content:
            return {"error": "Failed to retrieve listings page."}

        soup = BeautifulSoup(content, 'lxml')
        offers = soup.select('div.article-row')
        if not offers:
            logging.warning("No offers found on the listings page.")
            return {"error": "No offers found for this card."}

        seller_info_html = offers[0].select_one('.seller-name')
        if seller_info_html:
            logging.info(f"HTML of seller info for debugging: {seller_info_html.prettify()}")
        else:
            logging.info("Could not find '.seller-name' element for debugging.")

        best_offer = None
        min_total_price = float('inf')

        for offer in offers[:MAX_SELLERS_TO_CHECK]:
            seller_info_element = offer.select_one('.seller-name a')
            seller_name = seller_info_element.text.strip() if seller_info_element else "N/A"
            
            country_element = offer.select_one('.seller-name .fi')
            country = country_element['class'][1].split('-')[-1].upper() if country_element else "N/A"

            price_element = offer.select_one('.price-container, .price')
            price_text = price_element.text.strip() if price_element else "0,00 €"
            item_price = float(price_text.replace('.', '').replace(',', '.').replace('€', '').strip())

            # For now, shipping is a placeholder. Total price is item price.
            shipping_cost = 0 # Placeholder
            total_price = item_price

            seller_data = {
                "seller_name": seller_name,
                "country": country,
                "item_price": item_price,
                "shipping_cost": shipping_cost,
                "total_price": total_price
            }
            sellers_analyzed.append(seller_data)

            logging.info(f"Analyzed seller: {seller_name} ({country}) - Price: {item_price}€")

            if total_price < min_total_price:
                min_total_price = total_price
                best_offer = {
                    "card_name": card_name,
                    "seller_name": seller_name,
                    "country": country,
                    "item_price": item_price,
                    "shipping_cost": shipping_cost,
                    "total_price": total_price
                }
        
        # Save all analyzed sellers to a file
        with open('sellers_analyzed.json', 'w', encoding='utf-8') as f:
            json.dump(sellers_analyzed, f, ensure_ascii=False, indent=4)
        logging.info(f"Saved data for {len(sellers_analyzed)} sellers to sellers_analyzed.json")

        if best_offer:
            logging.info(f"Best offer found: {best_offer}")
            return best_offer
        else:
            logging.warning("Could not find any suitable offers.")
            return {"error": "Could not find any offers."}

    except Exception as e:
        logging.error(f"An unexpected error occurred in find_best_offer: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}

if __name__ == "__main__":
    logging.info("Scraper script started.")
    if len(sys.argv) < 2:
        logging.error("Usage: python scraper.py \"<card_name>\"")
        # Print JSON to stdout for the app to capture
        print(json.dumps({"error": "Usage: python scraper.py \"<card_name>\""}))
        sys.exit(1)
    
    card_name_arg = sys.argv[1]
    result = find_best_offer(card_name_arg)
    # The app expects the last line of stdout to be the JSON result
    print(json.dumps(result))
    logging.info("Scraper script finished.")
