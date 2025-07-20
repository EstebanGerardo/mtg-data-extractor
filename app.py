

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
    
# Display fetched cards status
if st.session_state.card_data:
    st.success(f"Successfully fetched {len(st.session_state.card_data)} cards!")
    
    with st.expander("View Fetched Card List"):
            # Create a DataFrame to display the cards with their prices and deck statistics
            display_data = []
            
            for card in st.session_state.card_data:
                # Extract data from the new nested structure
                card_info = {
                    'name': card['name'],
                    'deck_count': card.get('deck_count', 'N/A'),
                    'deck_percentage': card.get('deck_percentage', 'N/A'),
                    'total_decks': card.get('total_decks', 'N/A'),
                    'usd_price': card.get('usd_price', 'N/A'),
                    'eur_price': card.get('eur_price', 'N/A')
                }
                
                # Handle nested edhrec_data if present
                if 'edhrec_data' in card:
                    edhrec = card['edhrec_data']
                    card_info.update({
                        'deck_count': edhrec.get('deck_count', card_info['deck_count']),
                        'deck_percentage': edhrec.get('deck_percentage', card_info['deck_percentage']),
                        'total_decks': edhrec.get('total_decks', card_info['total_decks'])
                    })
                
                # Handle nested scryfall_prices if present
                if 'scryfall_prices' in card:
                    scryfall = card['scryfall_prices']
                    card_info.update({
                        'usd_price': scryfall.get('usd', card_info['usd_price']),
                        'eur_price': scryfall.get('eur', card_info['eur_price'])
                    })
                
                display_data.append(card_info)
            
            df_cards = pd.DataFrame(display_data)
            
            # Format the DataFrame for better display
            if not df_cards.empty:
                # Rename columns for better readability
                column_renames = {
                    "name": "Card Name",
                    "deck_count": "# of Decks",
                    "deck_percentage": "% of Decks",
                    "total_decks": "Total Decks",
                    "usd_price": "USD Price",
                    "eur_price": "EUR Price"
                }
                
                # Apply column renames
                df_cards = df_cards.rename(columns=column_renames)
                
                # Add a "Popularity Rank" column based on the order
                df_cards.insert(0, "Rank", range(1, len(df_cards) + 1))
                
                # Format price columns
                if "USD Price" in df_cards.columns:
                    df_cards["USD Price"] = df_cards["USD Price"].apply(
                        lambda x: f"${x:.2f}" if isinstance(x, (int, float)) and x is not None else "N/A"
                    )
                
                if "EUR Price" in df_cards.columns:
                    df_cards["EUR Price"] = df_cards["EUR Price"].apply(
                        lambda x: f"€{x:.2f}" if isinstance(x, (int, float)) and x is not None else "N/A"
                    )
                
                # Format deck count and total decks as integers with commas
                for col in ["# of Decks", "Total Decks"]:
                    if col in df_cards.columns:
                        df_cards[col] = df_cards[col].apply(
                            lambda x: f"{int(x):,}" if isinstance(x, (int, float)) and x is not None else "N/A"
                        )
                
                # Format percentage column
                if "% of Decks" in df_cards.columns:
                    df_cards["% of Decks"] = df_cards["% of Decks"].apply(
                        lambda x: f"{x}%" if isinstance(x, (int, float)) and x is not None else "N/A"
                    )
            
            # Display the formatted DataFrame
            st.dataframe(df_cards, use_container_width=True)
elif st.session_state.fetch_error:
    st.error(f"Failed to fetch card list. Error: {st.session_state.fetch_error}")
else:
    st.error("Failed to fetch card list. An unknown error occurred.")
    st.session_state.results = None # Clear previous results
    st.session_state.fetch_error = None

# Step 2: Analyze Prices (moved outside conditional)
st.header("Step 2: Analyze Prices")

# Show current card status
if st.session_state.card_data:
    st.info(f"📊 Ready to analyze {len(st.session_state.card_data)} fetched cards")
else:
    st.warning("⚠️ No cards fetched yet. Please fetch cards first.")

if st.button("Analyze Prices"):
        st.success("🎯 Button clicked! Starting analysis...")
        
        # Validate card data exists
        if not st.session_state.card_data:
            st.error("❌ No card data available. Please fetch cards first.")
        else:
            st.info(f"📊 Analyzing {len(st.session_state.card_data)} cards...")
            
            # Get currency rates
            st.info("💱 Fetching currency conversion rates...")
            usd_to_clp, eur_to_clp = get_currency_rates()
            
            if not usd_to_clp or not eur_to_clp:
                st.error("❌ Could not fetch currency rates. Please try again later.")
            else:
                st.success(f"✅ Currency rates: 1 USD = {usd_to_clp:,.0f} CLP, 1 EUR = {eur_to_clp:,.0f} CLP")
                
                # Perform analysis
                st.info("🔍 Calculating arbitrage opportunities...")
                results = []
                cards_with_prices = 0
                
                for card in st.session_state.card_data:
                    usd_price = card.get('usd_price', 0)
                    eur_price = card.get('eur_price', 0)
                    
                    if usd_price and eur_price:
                        cards_with_prices += 1
                        usd_clp = float(usd_price) * usd_to_clp
                        eur_clp = float(eur_price) * eur_to_clp
                        diff = usd_clp - eur_clp
                        diff_pct = (diff / eur_clp) * 100 if eur_clp > 0 else 0
                        
                        results.append({
                            'Card': card['name'],
                            'USD': f"${usd_price:.2f}",
                            'EUR': f"€{eur_price:.2f}", 
                            'USD (CLP)': f"{usd_clp:,.0f}",
                            'EUR (CLP)': f"{eur_clp:,.0f}",
                            'Difference (CLP)': f"{diff:+,.0f}",
                            'Difference %': f"{diff_pct:+.1f}%"
                        })
                
                if results:
                    st.success(f"🎉 Analysis complete! Found {len(results)} cards with price data ({cards_with_prices}/{len(st.session_state.card_data)} cards had both USD and EUR prices).")
                    
                    # Sort by absolute difference for better insights
                    results_df = pd.DataFrame(results)
                    results_df['abs_diff'] = results_df['Difference (CLP)'].str.replace(',', '').str.replace('+', '').str.replace('-', '').astype(float)
                    results_df = results_df.sort_values('abs_diff', ascending=False).drop('abs_diff', axis=1)
                    
                    st.dataframe(results_df, use_container_width=True)
                    st.session_state.results = results_df
                    
                    # Show summary
                    arbitrage_opportunities = len([r for r in results if abs(float(r['Difference (CLP)'].replace(',', '').replace('+', '').replace('-', ''))) > 1000])
                    st.info(f"📈 Summary: {arbitrage_opportunities} significant arbitrage opportunities found (>1000 CLP difference)")
                    
                else:
                    st.warning("⚠️ No cards with complete price data found for analysis.")

# --- Step 3: Display Results ---
if st.session_state.results is not None:
    st.markdown("---")
    st.header("Step 3: Price Analysis Results")
    
    # Sort by absolute difference to show biggest arbitrage opportunities first
    df_results = st.session_state.results.copy()
    
    # Convert difference strings back to numeric for sorting
    df_results['Difference_Numeric'] = df_results['Difference (CLP)'].str.replace(',', '').str.replace('$', '').astype(float)
    df_sorted = df_results.sort_values(by='Difference_Numeric', key=abs, ascending=False).reset_index(drop=True)
    
    # Remove the temporary numeric column
    df_sorted = df_sorted.drop('Difference_Numeric', axis=1)
    
    def color_difference(val):
        """Colors positive differences green and negative ones red."""
        try:
            numeric_val = float(val.replace(',', '').replace('$', ''))
            if numeric_val > 0:
                color = 'lightgreen'
            elif numeric_val < 0:
                color = 'lightcoral'
            else:
                color = 'white'
            return f'background-color: {color}'
        except:
            return 'background-color: white'

    def color_arbitrage(val):
        """Colors arbitrage opportunities."""
        if val == 'Yes':
            return 'background-color: lightblue'
        else:
            return 'background-color: white'

    # Apply styling only to existing columns
    styled_df = df_sorted.style.apply(lambda x: [color_difference(val) if col == 'Difference (CLP)' else '' for val in x], axis=0, subset=['Difference (CLP)'])
    
    st.dataframe(
        styled_df,
        height=500,
        use_container_width=True
    )
    
    # Add summary statistics
    st.subheader("Summary")
    total_cards = len(df_sorted)
    
    # Calculate arbitrage opportunities based on significant price differences (>1000 CLP)
    arbitrage_opportunities = len([index for index, row in df_sorted.iterrows() 
                                 if abs(float(row['Difference (CLP)'].replace(',', '').replace('+', '').replace('-', ''))) > 1000])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cards Analyzed", total_cards)
    with col2:
        st.metric("Arbitrage Opportunities", arbitrage_opportunities)
    with col3:
        percentage = (arbitrage_opportunities / total_cards * 100) if total_cards > 0 else 0
        st.metric("Opportunity Rate", f"{percentage:.1f}%")
