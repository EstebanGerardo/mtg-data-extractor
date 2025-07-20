

import streamlit as st
import pandas as pd
import time
from card_fetcher import get_top_commander_cards, get_currency_rates, get_card_prices
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log", mode='w'), # Overwrite log on each run
        logging.StreamHandler()
    ],
    force=True
)

st.set_page_config(page_title="Card Arbitrage Finder", layout="wide")

# Initialize session state
if 'card_data' not in st.session_state:
    st.session_state.card_data = []
if 'results' not in st.session_state:
    st.session_state.results = None
if 'fetch_error' not in st.session_state:
    st.session_state.fetch_error = None

# --- UI ---
st.title("MTG Card Arbitrage Finder")
st.markdown("""
This tool finds price differences for top EDHREC commander cards between Card Kingdom (USD) and Scryfall (representing Cardmarket in EUR), converting prices to Chilean Pesos (CLP).
""")

# --- Step 1: Get Top Cards ---
st.header("Step 1: Get Top Commander Cards")

time_period_option = st.radio(
    "Select time period:",
    ('Week', 'Month', 'All Time'),
    horizontal=True,
)

num_cards = st.number_input("How many top cards do you want to fetch?", min_value=1, max_value=100, value=100, step=1)

if st.button("Get Top Cards"):
    st.session_state.results = None # Clear previous results
    st.session_state.fetch_error = None
    with st.spinner("Fetching top cards from EDHREC..."):
        try:
            time_period = time_period_option.lower().replace(' ', '_')
            if time_period == 'all_time':
                time_period = 'all'
            st.session_state.card_data = get_top_commander_cards(time_period=time_period, num_cards=num_cards)
        except Exception as e:
            st.session_state.card_data = []
            st.session_state.fetch_error = str(e)
            logging.error(f"An exception occurred while fetching cards: {e}")
    
    if st.session_state.card_data:
        st.success(f"Successfully fetched {len(st.session_state.card_data)} cards!")
        # Remove the st.rerun() to allow the rest of the UI to render
        st.header("Step 2: Analyze Prices")
        
        with st.expander("View Fetched Card List"):
            # Create a DataFrame to display the cards with their prices and deck statistics
            df_cards = pd.DataFrame(st.session_state.card_data)
            
            # Format the DataFrame for better display
            if not df_cards.empty:
                # Rename columns for better readability
                column_renames = {
                    "name": "Card Name",
                    "cardkingdom_price": "CardKingdom Price",
                    "tcgplayer_price": "TCGplayer Price",
                    "starcitygames_price": "StarCityGames Price",
                    "deck_count": "# of Decks",
                    "deck_percentage": "% of Decks",
                    "total_decks": "Total Decks"
                }
                
                # Apply column renames where columns exist
                for old_col, new_col in column_renames.items():
                    if old_col in df_cards.columns:
                        df_cards = df_cards.rename(columns={old_col: new_col})
                
                # Add a "Popularity Rank" column based on the order
                df_cards.insert(0, "Rank", range(1, len(df_cards) + 1))
                
                # Format deck count and total decks as integers if they're numeric
                for col in df_cards.columns:
                    if col not in ["Card Name"]:
                        # Handle numeric conversion with proper exception handling
                        try:
                            df_cards[col] = pd.to_numeric(df_cards[col])
                            # Format numbers with commas if conversion succeeded
                            df_cards[col] = df_cards[col].apply(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) and not pd.isna(x) else x)
                        except (ValueError, TypeError):
                            # Keep as is if conversion fails
                            pass
                
                # Add % symbol to percentage column if it doesn't already have it
                if "% of Decks" in df_cards.columns:
                    df_cards["% of Decks"] = df_cards["% of Decks"].apply(lambda x: f"{x}%" if isinstance(x, str) and not x.endswith('%') and x != "N/A" else x)
            
            # Display the formatted DataFrame
            st.dataframe(df_cards, use_container_width=True)
    elif st.session_state.fetch_error:
        st.error(f"Failed to fetch card list. Error: {st.session_state.fetch_error}")
    else:
        st.error("Failed to fetch card list. An unknown error occurred.")
        st.session_state.results = None # Clear previous results
        st.session_state.fetch_error = None

    if st.button("Analyze Prices"):
        with st.spinner('Analyzing prices... This may take a moment.'):
            analysis_data = []
            progress_bar = st.progress(0)
            total_cards = len(st.session_state.card_data)

            usd_to_clp, eur_to_clp = get_currency_rates()
            if not usd_to_clp or not eur_to_clp:
                st.error("Could not fetch currency rates. Please try again later.")
                st.stop()

            for i, card_item in enumerate(st.session_state.card_data):
                card_name = card_item['name']
                
                # Extract all price points from EDHREC
                cardkingdom_price_str = card_item.get('cardkingdom_price', 'N/A')
                tcgplayer_price_str = card_item.get('tcgplayer_price', 'N/A')
                starcitygames_price_str = card_item.get('starcitygames_price', 'N/A')
                
                # Extract deck statistics
                deck_count = card_item.get('deck_count', 'N/A')
                deck_percentage = card_item.get('deck_percentage', 'N/A')
                total_decks = card_item.get('total_decks', 'N/A')
                
                # Try to extract numeric prices from EDHREC if available
                cardkingdom_usd = None
                tcgplayer_usd = None
                starcitygames_usd = None
                
                # Process CardKingdom price
                if cardkingdom_price_str != "N/A":
                    try:
                        cardkingdom_usd = float(cardkingdom_price_str.replace('$', ''))
                    except (ValueError, AttributeError):
                        cardkingdom_usd = None
                
                # Process TCGplayer price
                if tcgplayer_price_str != "N/A":
                    try:
                        tcgplayer_usd = float(tcgplayer_price_str.replace('$', ''))
                    except (ValueError, AttributeError):
                        tcgplayer_usd = None
                
                # Process StarCityGames price
                if starcitygames_price_str != "N/A":
                    try:
                        starcitygames_usd = float(starcitygames_price_str.replace('$', ''))
                    except (ValueError, AttributeError):
                        starcitygames_usd = None
                
                # Get prices from Scryfall API
                ck_price_usd, cm_price_eur = get_card_prices(card_name)
                
                if ck_price_usd and cm_price_eur:
                    ck_price_clp = float(ck_price_usd) * usd_to_clp
                    cm_price_clp = float(cm_price_eur) * eur_to_clp
                    difference = ck_price_clp - cm_price_clp
                    
                    # Calculate marketplace prices in CLP if available
                    cardkingdom_clp = None
                    tcgplayer_clp = None
                    starcitygames_clp = None
                    
                    if cardkingdom_usd:
                        cardkingdom_clp = cardkingdom_usd * usd_to_clp
                    if tcgplayer_usd:
                        tcgplayer_clp = tcgplayer_usd * usd_to_clp
                    if starcitygames_usd:
                        starcitygames_clp = starcitygames_usd * usd_to_clp
                    
                    # Calculate potential arbitrage opportunities
                    # Find the lowest price for comparison
                    best_online_price_usd = min([p for p in [cardkingdom_usd, tcgplayer_usd, starcitygames_usd] if p is not None], default=None)
                    best_online_price_clp = best_online_price_usd * usd_to_clp if best_online_price_usd else None
                    
                    # Calculate differences between different marketplaces
                    online_vs_ck_diff = best_online_price_clp - ck_price_clp if best_online_price_clp else None
                    online_vs_scryfall_diff = best_online_price_clp - cm_price_clp if best_online_price_clp else None
                    
                    analysis_data.append({
                        'Card Name': card_name,
                        'Deck Count': deck_count,
                        'Deck %': deck_percentage,
                        'CardKingdom (USD)': f"${cardkingdom_usd:.2f}" if cardkingdom_usd else "N/A",
                        'TCGplayer (USD)': f"${tcgplayer_usd:.2f}" if tcgplayer_usd else "N/A",
                        'StarCityGames (USD)': f"${starcitygames_usd:.2f}" if starcitygames_usd else "N/A",
                        'CardKingdom (CLP)': f"{cardkingdom_clp:,.0f}" if cardkingdom_clp else "N/A",
                        'TCGplayer (CLP)': f"{tcgplayer_clp:,.0f}" if tcgplayer_clp else "N/A",
                        'StarCityGames (CLP)': f"{starcitygames_clp:,.0f}" if starcitygames_clp else "N/A",
                        'Scryfall API (CLP)': f"{cm_price_clp:,.0f}",
                        'CK API (CLP)': f"{ck_price_clp:,.0f}",
                        'Best Online vs CK API': f"{online_vs_ck_diff:,.0f}" if online_vs_ck_diff else "N/A",
                        'Best Online vs Scryfall': f"{online_vs_scryfall_diff:,.0f}" if online_vs_scryfall_diff else "N/A"
                    })
                
                time.sleep(0.1) # Respect Scryfall API rate limit
                progress_bar.progress((i + 1) / total_cards, text=f"Analyzing {card_name}...")
            
            if analysis_data:
                st.session_state.results = pd.DataFrame(analysis_data)
                st.rerun()
            else:
                st.session_state.results = None
                st.warning("Could not retrieve price data for any of the cards.")

# --- Step 3: Display Results ---
if st.session_state.results is not None:
    st.markdown("---")
    st.header("Step 3: Price Analysis Results")
    
    df_sorted = st.session_state.results.sort_values(by='Difference (CLP)', ascending=False).reset_index(drop=True)
    
    def color_difference(val):
        """Colors positive differences green and negative ones red."""
        if val > 0:
            color = 'lightgreen'
        elif val < 0:
            color = 'lightcoral'
        else:
            color = 'white'
        return f'background-color: {color}'

    # Apply styling
    st.dataframe(
        df_sorted.style.apply(color_difference, subset=['Difference (CLP)'])
                       .format({
                           'CK Price (CLP)': '{:,.0f}',
                           'Scryfall Price (CLP)': '{:,.0f}',
                           'Difference (CLP)': '{:,.0f}'
                       }),
        height=500,
        use_container_width=True
    )
