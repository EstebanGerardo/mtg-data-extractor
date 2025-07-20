# MTG Cardmarket Scraper

This project is a Python-based web scraper designed to find the best price for Magic: The Gathering cards on [Cardmarket](https://www.cardmarket.com/en/Magic). It analyzes offers from multiple sellers and identifies the most cost-effective option.

## Features

- **Card Price Scraping**: Fetches data for any specified Magic: The Gathering card.
- **Seller Analysis**: Analyzes up to 50 sellers to find the best offer.
- **Country Detection**: Correctly identifies the seller's country.
- **Cloudflare Bypass**: Uses ScraperAPI to handle Cloudflare challenges and JavaScript rendering.
- **Data Export**: Saves a detailed list of all analyzed sellers to `sellers_analyzed.json`.
- **Robust Error Handling**: Includes retries and detailed logging for reliable execution.

## Setup and Installation

Follow these steps to set up the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/EstebanGerardo/mtg-data-extractor.git
cd mtg-data-extractor
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

Install the required Python packages.

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

The scraper requires a ScraperAPI key to function. 

1.  Sign up for a free account at [ScraperAPI](https://www.scraperapi.com/) to get your API key.
2.  Rename the `.env.example` file to `.env`.
3.  Open the `.env` file and add your API key:

```
SCRAPERAPI_KEY="YOUR_SCRAPERAPI_KEY_HERE"
```

## Usage

To run the scraper, execute the `scraper.py` script from your terminal with the card name as an argument. Make sure to enclose the card name in quotes if it contains spaces.

```bash
python scraper.py "Sol Ring"
```

After the script finishes, it will:
- Print the best offer found to the console in JSON format.
- Create a `sellers_analyzed.json` file with data from all the sellers it checked.
- Create a `scraper.log` file with detailed logs of the scraping process.