import streamlit as st
import pandas as pd
from card_fetcher import get_top_commander_cards, get_currency_rates, get_card_prices
import logging

# Configure logging to write to scraper.log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler() # Also print to console
    ],
    force=True # Override any existing Streamlit logging configurations
)

st.set_page_config(page_title="Card Arbitrage Finder", layout="wide")

# Initialize session state
if 'card_list' not in st.session_state:
    st.session_state.card_list = []
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- UI ---
st.title("Card Arbitrage Finder")
st.markdown("This tool helps you find price differences for Magic: The Gathering cards between Cardmarket (Europe) and Card Kingdom (North America), converted to Chilean Pesos (CLP).")

# --- Step 1: Get Top Cards ---
st.header("Step 1: Get Top Commander Cards")
num_cards = st.number_input("How many top cards do you want to fetch from EDHREC?", min_value=10, max_value=200, value=50, step=10)

if st.button("Get Top Cards"):
    with st.spinner("Fetching card list from EDHREC..."):
        st.session_state.card_list = get_top_commander_cards(num_cards)
    
    if st.session_state.card_list:
        st.success(f"Successfully fetched {len(st.session_state.card_list)} cards!")
        st.session_state.step = 2
    else:
        st.error("Failed to fetch card list. EDHREC might be temporarily unavailable or the page structure has changed. Please try again later.")

# --- Step 2: Find Arbitrage Opportunities ---
if st.session_state.step == 2:
    st.markdown("---")
    st.header("Step 2: Price Analysis")

    with st.expander("View Fetched Card List"):
        st.write(st.session_state.card_list)

    if st.button("Find Arbitrage Opportunities"):
        with st.spinner("Fetching currency exchange rates..."):
            usd_to_clp, eur_to_clp = get_currency_rates()
        
        if not usd_to_clp or not eur_to_clp:
            st.error("Could not fetch currency rates. Please try again later.")
        else:
            st.success(f"Current Rates: 1 USD = {usd_to_clp:.2f} CLP, 1 EUR = {eur_to_clp:.2f} CLP")
            results = []
            progress_bar = st.progress(0)
            total_cards = len(st.session_state.card_list)

            for i, card_name in enumerate(st.session_state.card_list):
                ck_price_usd, cm_price_eur = get_card_prices(card_name)
                
                if ck_price_usd and cm_price_eur:
                    ck_price_clp = float(ck_price_usd) * usd_to_clp
                    cm_price_clp = float(cm_price_eur) * eur_to_clp
                    difference = ck_price_clp - cm_price_clp
                    
                    results.append({
                        "Card Name": card_name,
                        "Card Kingdom Price (CLP)": ck_price_clp,
                        "Cardmarket Price (CLP)": cm_price_clp,
                        "Difference (CLP)": difference
                    })
                progress_bar.progress((i + 1) / total_cards)

            if results:
                df = pd.DataFrame(results)
                df_sorted = df.sort_values(by="Difference (CLP)", ascending=False).reset_index(drop=True)

                # Color-coding for the 'Difference (CLP)' column
                def color_difference(val):
                    color = 'green' if val > 0 else 'red' if val < 0 else 'white'
                    return f'color: {color}'

                st.dataframe(df_sorted.style.applymap(color_difference, subset=['Difference (CLP)'])
                                       .format({
                                           'Card Kingdom Price (CLP)': '{:,.0f}',
                                           'Cardmarket Price (CLP)': '{:,.0f}',
                                           'Difference (CLP)': '{:,.0f}'
                                       }), height=500)
            else:
                st.warning("Could not retrieve price data for any of the cards.")
