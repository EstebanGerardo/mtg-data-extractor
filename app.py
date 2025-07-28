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

st.set_page_config(
    page_title="MTG Singles - Card Management", 
    page_icon="⬜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication
auth_manager = create_auth_manager()

# Require authentication before accessing the app
if not auth_manager.require_auth():
    st.stop()

# Professional sidebar design
with st.sidebar:
    # Professional sidebar header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #581c87 0%, #8b5cf6 100%); 
                padding: 1.5rem 1rem; border-radius: 8px; margin-bottom: 1.5rem; color: white; text-align: center;">
        <h3 style="margin: 0; font-size: 1.2rem;">■ MTG Singles</h3>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">Card Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    # User information with professional styling
    user_info = auth_manager.get_user_info()
    st.markdown("""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <h4 style="color: #581c87; margin: 0 0 0.5rem 0;">○ User Profile</h4>
        <p style="margin: 0; color: #64748b;"><strong>Name:</strong> {}</p>
        <p style="margin: 0.25rem 0 0 0; color: #64748b;"><strong>Username:</strong> {}</p>
    </div>
    """.format(user_info['name'], user_info['username']), unsafe_allow_html=True)
    
    # Logout button
    auth_manager.logout()

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

# --- PROFESSIONAL UI HEADER ---
# Custom CSS for minimalistic professional design
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #581c87 0%, #8b5cf6 100%);
    padding: 2rem 1.5rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
}
.main-header h1 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 600;
    letter-spacing: -0.025em;
}
.main-header p {
    margin: 0.5rem 0 0 0;
    font-size: 1.1rem;
    opacity: 0.9;
}
.step-container {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
}
.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# Main header with professional styling
st.markdown("""
<div class="main-header">
    <h1>■ MTG Singles - Card Management</h1>
    <p>Professional card arbitrage analysis and portfolio management</p>
</div>
""", unsafe_allow_html=True)

# Professional dashboard metrics
watchlist_summary = get_watchlist_summary()
if watchlist_summary['total_cards'] > 0:
    st.markdown("### ▦ Portfolio Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #581c87; margin: 0;">{}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #64748b;">Total Cards</p>
        </div>
        """.format(watchlist_summary['total_cards']), unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #059669; margin: 0;">{}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #64748b;">Opportunities</p>
        </div>
        """.format(watchlist_summary['good_opportunities']), unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #7c3aed; margin: 0;">{}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #64748b;">Added Today</p>
        </div>
        """.format(watchlist_summary['recent_additions']), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- TAB-BASED WORKFLOW NAVIGATION ---
st.markdown("### ▶ Workflow Navigation")

# Step status indicators for dynamic tab labels
step1_status = "■" if st.session_state.card_data else "○"
step2_status = "■" if st.session_state.results is not None else "○"
step3_status = "■" if st.session_state.get('selected_cards') else "○"

# Create professional tabs with status indicators
tab1, tab2, tab3 = st.tabs([
    f"{step1_status} Step 1: Data Extraction",
    f"{step2_status} Step 2: Price Analysis", 
    f"{step3_status} Step 3: Portfolio Management"
])

# --- TAB 1: DATA EXTRACTION ---
with tab1:
    st.markdown("#### ▦ Configure Card Extraction")
    st.markdown("Extract top commander cards from EDHREC for analysis")
    
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

# --- TAB 2: PRICE ANALYSIS & SELECTION ---
with tab2:
    st.markdown("#### ▦ Price Analysis & Card Selection")
    st.markdown("Analyze arbitrage opportunities and select cards for your watchlist")
    
    # Show current card status
    if st.session_state.card_data:
        st.info(f"▦ Ready to analyze {len(st.session_state.card_data)} fetched cards")
    else:
        st.warning("○ No cards fetched yet. Please fetch cards first.")

    # CLP Threshold Configuration
    st.markdown("##### ▦ Opportunity Threshold")
    clp_threshold = st.number_input(
        "CLP threshold for opportunities (only EU < USD):",
        min_value=0,
        value=1000,
        step=100,
        help="Minimum CLP difference to consider as an opportunity. Only cards where EU price is less than USD price will be considered."
    )

    if st.button("Analyze Prices"):
        st.success("▶ Button clicked! Starting analysis...")
        
        # Validate card data exists
        if not st.session_state.card_data:
            st.error("❌ No card data available. Please fetch cards first.")
        else:
            st.info(f"▦ Analyzing {len(st.session_state.card_data)} cards...")
            
            # Get currency rates
            st.info("▦ Fetching currency conversion rates...")
            usd_to_clp, eur_to_clp = get_currency_rates()
        
            if not usd_to_clp or not eur_to_clp:
                st.error("❌ Could not fetch currency rates. Please try again later.")
            else:
                st.success(f"■ Currency rates: 1 USD = {usd_to_clp:,.0f} CLP, 1 EUR = {eur_to_clp:,.0f} CLP")
                
                # Update extraction metadata with currency rates
                st.session_state.extraction_metadata.update({
                    'usd_to_clp_rate': usd_to_clp,
                    'eur_to_clp_rate': eur_to_clp,
                    'num_cards_with_prices': 0  # Will be updated below
                })
            
                # Perform analysis
                st.info("▦ Calculating arbitrage opportunities...")
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
                    st.success(f"■ Analysis complete! Found {len(results)} cards with price data ({cards_with_prices}/{len(st.session_state.card_data)} cards had both USD and EUR prices).")
                    
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
                    st.info(f"▦ **Currency Rates Used:** 1 USD = {usd_to_clp:,.0f} CLP | 1 EUR = {eur_to_clp:,.0f} CLP")
                    
                    # Show summary
                    good_opportunities = len([r for r in results if r['Good Opportunity'] == 'Yes'])
                    st.info(f"▦ Summary: {good_opportunities} good arbitrage opportunities found (EU < USD, ≥{clp_threshold:,.0f} CLP difference)")
                    
                    # Enable card selection interface
                    st.session_state.show_selection = True
                    
                    # Show card selection button to make it clear
                    st.success("▶ Ready for card selection! Continue to card selection below.")
                    
                else:
                    st.warning("○ No cards with complete price data found for analysis.")

    # --- Card Selection Interface ---
    # Always show card selection interface when results are available
    if st.session_state.results is not None:
        st.markdown("##### ▦ Card Selection")
        
        # Automatically show card selection interface
        try:
            selected_cards = display_card_selection_interface(
                st.session_state.results, 
                st.session_state.extraction_metadata
            )
            
            if selected_cards:
                st.session_state.selected_cards = selected_cards
                # Don't hide the interface, keep it visible for reference
                st.success(f"■ Successfully processed {len(selected_cards)} selected cards!")
                    
        except Exception as e:
            st.error(f"Error in card selection interface: {e}")
            logging.error(f"Card selection interface error: {e}")

# --- TAB 3: PORTFOLIO MANAGEMENT ---
with tab3:
    st.markdown("#### ▦ Portfolio Management")
    st.markdown("Track and manage your card investments")
    
    # Always show watchlist overview section
    try:
        display_watchlist_overview()
    except Exception as e:
        st.error(f"Error displaying watchlist overview: {e}")
        logging.error(f"Watchlist overview error: {e}")

# Legacy section removed - functionality now integrated into the persistent step-by-step workflow above
