import streamlit as st
import pandas as pd
import time
from card_fetcher import get_top_commander_cards, get_currency_rates, get_card_prices
from database import init_database, get_database_stats
from watchlist_manager import (
    display_card_selection_interface, display_watchlist_overview, 
    get_watchlist_summary, update_watchlist_prices
)
from auth import create_auth_manager
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

st.set_page_config(page_title="MTG Card Arbitrage Finder", layout="wide")

# Initialize authentication
auth_manager = create_auth_manager()

# Require authentication before accessing the app
if not auth_manager.require_auth():
    st.stop()

# Display user info and logout in sidebar
with st.sidebar:
    user_info = auth_manager.get_user_info()
    st.markdown(f"### 👤 Welcome, {user_info['name']}!")
    st.markdown(f"**Username:** {user_info['username']}")
    st.markdown("---")
    auth_manager.logout()
    st.markdown("---")

# Initialize database
try:
    init_database()
except Exception as e:
    st.error(f"Failed to initialize database: {e}")
    st.stop()

# Initialize session state
if 'card_data' not in st.session_state:
    st.session_state.card_data = []
if 'results' not in st.session_state:
    st.session_state.results = None
if 'fetch_error' not in st.session_state:
    st.session_state.fetch_error = None
if 'extraction_metadata' not in st.session_state:
    st.session_state.extraction_metadata = {}
if 'selected_cards' not in st.session_state:
    st.session_state.selected_cards = []
if 'show_selection' not in st.session_state:
    st.session_state.show_selection = False

# --- UI ---
st.title("MTG Card Arbitrage Finder")
st.markdown("""
This tool helps you find and track MTG card arbitrage opportunities through a 3-step process:
1. **Extract & Analyze**: Get top EDHREC commander cards and analyze price differences
2. **Select Cards**: Choose which cards to add to your personal watchlist for tracking
3. **Track Over Time**: Monitor your selected cards and analyze historical price trends
""")

# Display watchlist summary
watchlist_summary = get_watchlist_summary()
if watchlist_summary['total_cards'] > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Watchlist Cards", watchlist_summary['total_cards'])
    with col2:
        st.metric("Good Opportunities", watchlist_summary['good_opportunities'])
    with col3:
        st.metric("Added Today", watchlist_summary['recent_additions'])

# --- PERSISTENT STEP HEADERS ---
st.markdown("## 🎯 MTG Card Arbitrage Workflow")

# Step 1 Header - Always visible
step1_status = "✅" if st.session_state.card_data else "⏳"
st.markdown(f"### {step1_status} Step 1: Fetch Top Commander Cards")

# Step 2 Header - Always visible
step2_status = "✅" if st.session_state.results is not None else "⏳" if st.session_state.card_data else "⏸️"
st.markdown(f"### {step2_status} Step 2: Analyze Prices & Select Cards")

# Step 3 Header - Always visible
step3_status = "✅" if st.session_state.get('selected_cards') else "⏳" if st.session_state.results is not None else "⏸️"
st.markdown(f"### {step3_status} Step 3: Watchlist Overview")

st.divider()

# --- Step 1 Content ---
st.subheader("📊 Configure Card Extraction")

time_period_option = st.radio(
    "Select time period:",
    ('Week', 'Month', 'Last 2 years'),
    horizontal=True,
)

num_cards = st.number_input("How many top cards do you want to fetch?", min_value=1, max_value=100, value=100, step=1)

if st.button("Get Top Cards"):
    st.session_state.results = None # Clear previous results
    st.session_state.fetch_error = None
    st.session_state.show_selection = False # Reset selection interface
    st.session_state.selected_cards = [] # Clear previous selections
    
    with st.spinner("Fetching top cards from EDHREC..."):
        try:
            time_period = time_period_option.lower().replace(' ', '_')
            if time_period == 'last_2_years':
                time_period = '2years'
            st.session_state.card_data = get_top_commander_cards(time_period=time_period, num_cards=num_cards)
            
            # Store extraction metadata
            st.session_state.extraction_metadata = {
                'time_period': time_period,
                'num_cards_extracted': len(st.session_state.card_data),
                'extraction_date': pd.Timestamp.now().isoformat()
            }
            
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
# No else block - don't show error on first load when no fetch has been attempted

st.divider()

# --- Step 2 Content ---
st.subheader("💰 Price Analysis & Card Selection")

# Show current card status
if st.session_state.card_data:
    st.info(f"📆 Ready to analyze {len(st.session_state.card_data)} fetched cards")
else:
    st.warning("⚠️ No cards fetched yet. Please fetch cards first.")

# CLP Threshold Configuration
st.subheader("💰 Opportunity Threshold")
clp_threshold = st.number_input(
    "CLP threshold for opportunities (only EU < USD):",
    min_value=0,
    value=1000,
    step=100,
    help="Minimum CLP difference to consider as an opportunity. Only cards where EU price is less than USD price will be considered."
)

if st.button("Analyze Prices"):
    st.success("🎯 Button clicked! Starting analysis...")
    
    # Validate card data exists
    if not st.session_state.card_data:
        st.error("❌ No card data available. Please fetch cards first.")
    else:
        st.info(f"📆 Analyzing {len(st.session_state.card_data)} cards...")
        
        # Get currency rates
        st.info("💱 Fetching currency conversion rates...")
        usd_to_clp, eur_to_clp = get_currency_rates()
        
        if not usd_to_clp or not eur_to_clp:
            st.error("❌ Could not fetch currency rates. Please try again later.")
        else:
            st.success(f"✅ Currency rates: 1 USD = {usd_to_clp:,.0f} CLP, 1 EUR = {eur_to_clp:,.0f} CLP")
            
            # Update extraction metadata with currency rates
            st.session_state.extraction_metadata.update({
                'usd_to_clp_rate': usd_to_clp,
                'eur_to_clp_rate': eur_to_clp,
                'num_cards_with_prices': 0  # Will be updated below
            })
            
            # Perform analysis
            st.info("🔍 Calculating arbitrage opportunities...")
            results = []
            cards_with_prices = 0
            
            for card in st.session_state.card_data:
                usd_price = card.get('usd_price', 0)
                eur_price = card.get('eur_price', 0)
                
                if usd_price and eur_price:
                    cards_with_prices += 1
                    
                    # Convert to CLP
                    usd_clp = usd_price * usd_to_clp
                    eur_clp = eur_price * eur_to_clp
                    diff = usd_clp - eur_clp
                    diff_pct = (diff / usd_clp * 100) if usd_clp > 0 else 0
                    
                    # Check if this is a good opportunity (EU < USD and difference > threshold)
                    is_opportunity = eur_clp < usd_clp and diff >= clp_threshold
                    
                    results.append({
                        'Card Name': card['name'],
                        'USD (CLP)': f"{usd_clp:,.0f}",
                        'EUR (CLP)': f"{eur_clp:,.0f}",
                        'Difference (CLP)': f"{diff:+,.0f}",
                        'Difference %': f"{diff_pct:+.1f}%",
                        'Good Opportunity': 'Yes' if is_opportunity else 'No'
                    })
            
            if results:
                st.success(f"🎉 Analysis complete! Found {len(results)} cards with price data ({cards_with_prices}/{len(st.session_state.card_data)} cards had both USD and EUR prices).")
                
                # Update extraction metadata with analysis parameters
                st.session_state.extraction_metadata['num_cards_with_prices'] = cards_with_prices
                st.session_state.extraction_metadata['clp_threshold'] = clp_threshold
                st.session_state.extraction_metadata['analysis_date'] = pd.Timestamp.now().isoformat()
                
                # Sort by absolute difference for better insights
                results_df = pd.DataFrame(results)
                results_df['abs_diff'] = results_df['Difference (CLP)'].str.replace(',', '').str.replace('+', '').str.replace('-', '').astype(float)
                results_df = results_df.sort_values('abs_diff', ascending=False).drop('abs_diff', axis=1)
                
                st.dataframe(results_df, use_container_width=True)
                st.session_state.results = results_df
                
                # Show currency rates used in analysis
                st.info(f"💱 **Currency Rates Used:** 1 USD = {usd_to_clp:,.0f} CLP | 1 EUR = {eur_to_clp:,.0f} CLP")
                
                # Show summary
                good_opportunities = len([r for r in results if r['Good Opportunity'] == 'Yes'])
                st.info(f"📈 Summary: {good_opportunities} good arbitrage opportunities found (EU < USD, ≥{clp_threshold:,.0f} CLP difference)")
                
                # Enable card selection interface
                st.session_state.show_selection = True
                
                # Show card selection button to make it clear
                st.success("🎯 Ready for card selection! Scroll down to Step 2: Select Cards for Watchlist")
                
            else:
                st.warning("⚠️ No cards with complete price data found for analysis.")

# --- Card Selection Interface ---
# Always show card selection interface when results are available
if st.session_state.results is not None:
    # Debug information (can be removed later)
    st.write(f"🔧 Debug: Results available, show_selection = {st.session_state.get('show_selection', False)}")
    
    # Automatically show card selection interface
    try:
        selected_cards = display_card_selection_interface(
            st.session_state.results, 
            st.session_state.extraction_metadata
        )
        
        if selected_cards:
            st.session_state.selected_cards = selected_cards
            # Don't hide the interface, keep it visible for reference
            st.success(f"✅ Successfully processed {len(selected_cards)} selected cards!")
            
    except Exception as e:
        st.error(f"Error in card selection interface: {e}")
        logging.error(f"Card selection interface error: {e}")

st.divider()

# --- Step 3 Content ---
st.subheader("📋 Watchlist Management")

# Always show watchlist overview section
try:
    display_watchlist_overview()
except Exception as e:
    st.error(f"Error displaying watchlist overview: {e}")
    logging.error(f"Watchlist overview error: {e}")

# Legacy section removed - functionality now integrated into the persistent step-by-step workflow above
