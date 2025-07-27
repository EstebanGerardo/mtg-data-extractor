"""
Watchlist Manager module for MTG Card Data Extractor.
Handles card selection, watchlist management, and data processing.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
import logging
from database import (
    add_card_to_watchlist, save_price_data, get_watchlist_cards,
    get_card_price_history, remove_card_from_watchlist,
    save_extraction_session, update_extraction_session_selections,
    save_selection_history, get_database_stats
)

def display_card_selection_interface(results_df: pd.DataFrame, 
                                   extraction_metadata: Dict) -> List[Dict]:
    """
    Display the card selection interface after price analysis.
    Returns list of selected cards with their data.
    """
    st.markdown("---")
    st.header("Step 2: Select Cards for Watchlist")
    st.markdown("""
    Choose which cards you want to track over time. Only selected cards will be saved to your personal watchlist database for future analysis.
    """)
    
    if results_df.empty:
        st.warning("No cards available for selection.")
        return []
    
    # Initialize selection state if not exists
    if 'card_selections' not in st.session_state:
        st.session_state.card_selections = {}
    
    # Create a copy of the dataframe for selection
    selection_df = results_df.copy()
    
    # Add selection controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Select All Good Opportunities"):
            for idx in selection_df.index:
                card_name = selection_df.loc[idx, 'Card Name']
                if selection_df.loc[idx, 'Good Opportunity'] == 'Yes':
                    st.session_state.card_selections[card_name] = True
    
    with col2:
        if st.button("Select All"):
            for idx in selection_df.index:
                card_name = selection_df.loc[idx, 'Card Name']
                st.session_state.card_selections[card_name] = True
    
    with col3:
        if st.button("Deselect All"):
            st.session_state.card_selections = {}
    
    with col4:
        if st.button("Select Top 10"):
            for i, idx in enumerate(selection_df.index[:10]):
                card_name = selection_df.loc[idx, 'Card Name']
                st.session_state.card_selections[card_name] = True
    
    # Search and Filter Controls
    st.subheader("🔍 Search & Filter Cards")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input(
            "Search card names:",
            placeholder="Type card name to search...",
            help="Filter cards by name"
        )
    
    with col2:
        show_only_opportunities = st.checkbox(
            "Only Good Opportunities",
            value=False,
            help="Show only cards with good arbitrage opportunities"
        )
    
    with col3:
        min_difference = st.number_input(
            "Min CLP Difference:",
            min_value=0,
            value=0,
            step=500,
            help="Filter by minimum price difference"
        )
    
    # Apply filters
    filtered_df = selection_df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['Card Name'].str.contains(search_term, case=False, na=False)]
    
    if show_only_opportunities:
        filtered_df = filtered_df[filtered_df['Good Opportunity'] == 'Yes']
    
    if min_difference > 0:
        # Extract numeric values from difference column
        filtered_df['diff_numeric'] = filtered_df['Difference (CLP)'].str.replace(',', '').str.replace('+', '').str.replace('-', '').astype(float)
        filtered_df = filtered_df[filtered_df['diff_numeric'] >= min_difference]
        filtered_df = filtered_df.drop('diff_numeric', axis=1)
    
    # Display filtered results count
    st.info(f"📊 Showing {len(filtered_df)} of {len(selection_df)} cards")
    
    # Interactive Card Selection Table
    st.subheader("📋 Select Cards for Watchlist")
    
    if filtered_df.empty:
        st.warning("No cards match your filters. Try adjusting your search criteria.")
        selected_cards = []
    else:
        # Create selection interface with individual checkboxes
        selected_cards = []
        
        # Display cards in a more manageable format
        for idx, row in filtered_df.iterrows():
            card_name = row['Card Name']
            
            # Initialize selection state for this card if not exists
            if card_name not in st.session_state.card_selections:
                # Auto-select good opportunities by default
                st.session_state.card_selections[card_name] = (row['Good Opportunity'] == 'Yes')
            
            # Create a container for each card
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1, 1, 1])
                
                with col1:
                    # Opportunity indicator
                    if row['Good Opportunity'] == 'Yes':
                        st.markdown("🟢")
                    else:
                        st.markdown("⚪")
                
                with col2:
                    # Card name with checkbox
                    is_selected = st.checkbox(
                        f"**{card_name}**",
                        value=st.session_state.card_selections[card_name],
                        key=f"select_{card_name}_{idx}"
                    )
                    st.session_state.card_selections[card_name] = is_selected
                
                with col3:
                    st.text(f"USD: {row['USD (CLP)']}")
                
                with col4:
                    st.text(f"EUR: {row['EUR (CLP)']}")
                
                with col5:
                    # Color-code the difference
                    diff_text = f"Diff: {row['Difference (CLP)']}"
                    if row['Good Opportunity'] == 'Yes':
                        st.markdown(f"**:green[{diff_text}]**")
                    else:
                        st.text(diff_text)
                
                # Add selected card to list
                if is_selected:
                    selected_cards.append({
                        'card_name': card_name,
                        'usd_price': float(row['USD (CLP)'].replace(',', '')) if row['USD (CLP)'] != 'N/A' else None,
                        'eur_price': float(row['EUR (CLP)'].replace(',', '')) if row['EUR (CLP)'] != 'N/A' else None,
                        'usd_clp': float(row['USD (CLP)'].replace(',', '')) if row['USD (CLP)'] != 'N/A' else None,
                        'eur_clp': float(row['EUR (CLP)'].replace(',', '')) if row['EUR (CLP)'] != 'N/A' else None,
                        'price_difference_clp': float(row['Difference (CLP)'].replace(',', '').replace('+', '').replace('-', '')),
                        'is_good_opportunity': row['Good Opportunity'] == 'Yes',
                        'was_selected': True
                    })
                
                # Add a subtle separator
                if idx < len(filtered_df) - 1:
                    st.markdown("<hr style='margin: 5px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
    
    # Show selection summary
    if selected_cards:
        st.success(f"✅ {len(selected_cards)} cards selected for watchlist")
        
        # Notes section for selected cards
        st.subheader("Add Notes (Optional)")
        notes = st.text_area(
            "Add notes about why you're tracking these cards:",
            placeholder="e.g., For my Voltron deck, good investment potential, etc.",
            height=100
        )
        
        # Save to watchlist button
        if st.button("💾 Save Selected Cards to Watchlist", type="primary"):
            return save_selected_cards_to_watchlist(
                selected_cards, 
                notes, 
                extraction_metadata,
                results_df
            )
    else:
        st.info("No cards selected. Use the checkboxes above to select cards for your watchlist.")
    
    return selected_cards

def save_selected_cards_to_watchlist(selected_cards: List[Dict], 
                                   notes: str,
                                   extraction_metadata: Dict,
                                   all_results_df: pd.DataFrame) -> List[Dict]:
    """Save selected cards to the watchlist database."""
    
    try:
        # Save extraction session
        session_id = save_extraction_session(
            time_period=extraction_metadata.get('time_period', 'unknown'),
            num_cards_extracted=extraction_metadata.get('num_cards_extracted', 0),
            num_cards_with_prices=extraction_metadata.get('num_cards_with_prices', 0),
            clp_threshold=extraction_metadata.get('clp_threshold', 0)
        )
        
        # Save selected cards to watchlist
        saved_cards = []
        for card_data in selected_cards:
            try:
                # Add card to watchlist
                card_id = add_card_to_watchlist(card_data['card_name'], notes)
                
                # Prepare price data
                price_data = {
                    'usd_price': card_data.get('usd_price'),
                    'eur_price': card_data.get('eur_price'),
                    'usd_clp': card_data.get('usd_clp'),
                    'eur_clp': card_data.get('eur_clp'),
                    'price_difference_clp': card_data.get('price_difference_clp'),
                    'usd_to_clp_rate': extraction_metadata.get('usd_to_clp_rate'),
                    'eur_to_clp_rate': extraction_metadata.get('eur_to_clp_rate'),
                    'is_good_opportunity': card_data.get('is_good_opportunity', False),
                    'clp_threshold_used': extraction_metadata.get('clp_threshold', 0),
                    'deck_count': extraction_metadata.get('deck_count'),
                    'deck_percentage': extraction_metadata.get('deck_percentage')
                }
                
                # Save price data
                if save_price_data(card_id, price_data):
                    saved_cards.append({
                        'card_id': card_id,
                        'card_name': card_data['card_name'],
                        'notes': notes
                    })
                    
            except Exception as e:
                logging.error(f"Error saving card {card_data['card_name']}: {e}")
                st.error(f"Failed to save {card_data['card_name']}: {str(e)}")
        
        # Update session with number of selected cards
        update_extraction_session_selections(session_id, len(saved_cards))
        
        # Save selection history for all cards (selected and not selected)
        all_cards_history = []
        for _, row in all_results_df.iterrows():
            card_history = {
                'card_name': row['Card Name'],
                'was_selected': any(card['card_name'] == row['Card Name'] for card in selected_cards),
                'usd_price': float(row['USD (CLP)'].replace(',', '')) if row['USD (CLP)'] != 'N/A' else None,
                'eur_price': float(row['EUR (CLP)'].replace(',', '')) if row['EUR (CLP)'] != 'N/A' else None,
                'price_difference_clp': float(row['Difference (CLP)'].replace(',', '').replace('+', '').replace('-', '')),
                'is_good_opportunity': row['Good Opportunity'] == 'Yes'
            }
            all_cards_history.append(card_history)
        
        save_selection_history(session_id, all_cards_history)
        
        # Show success message
        if saved_cards:
            st.success(f"🎉 Successfully saved {len(saved_cards)} cards to your watchlist!")
            
            # Display saved cards summary
            with st.expander("View Saved Cards"):
                for card in saved_cards:
                    st.write(f"✅ **{card['card_name']}** (ID: {card['card_id']})")
            
            # Clear selection state
            clear_selection_state()
            
        return saved_cards
        
    except Exception as e:
        logging.error(f"Error saving cards to watchlist: {e}")
        st.error(f"Failed to save cards to watchlist: {str(e)}")
        return []

def clear_selection_state():
    """Clear all selection checkboxes from session state."""
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith('select_')]
    for key in keys_to_remove:
        del st.session_state[key]

def display_watchlist_overview():
    """Display the current watchlist overview."""
    st.header("Step 3: Watchlist Overview")
    
    try:
        # Get database stats first
        db_stats = get_database_stats()
        
        # Display database status
        if db_stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Cards", db_stats.get('active_watchlist_cards', 0))
            with col2:
                st.metric("Price Records", db_stats.get('total_price_records', 0))
            with col3:
                st.metric("Sessions", db_stats.get('extraction_sessions', 0))
        
        watchlist_cards = get_watchlist_cards()
        
        if not watchlist_cards:
            st.info("📝 Your watchlist is empty. Add some cards by running an extraction and selecting cards to track.")
            st.markdown("""
            **How to add cards to your watchlist:**
            1. Run Step 1: Extract cards from EDHREC
            2. Run Step 2: Analyze prices
            3. Select cards you want to track using the multiselect dropdown
            4. Click "Save Selected Cards to Watchlist"
            """)
            return
        
        st.success(f"📊 You are currently tracking {len(watchlist_cards)} cards")
        
    except Exception as e:
        st.error(f"Error getting watchlist data: {e}")
        logging.error(f"Watchlist overview error: {e}")
        return
    
    # Display watchlist cards
    for card in watchlist_cards:
        with st.expander(f"📊 {card['name']} (Added: {card['date_added'][:10]})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Notes:** {card['notes'] or 'No notes'}")
                
                # Get recent price history
                price_history = get_card_price_history(card['id'], days=30)
                if price_history:
                    latest_price = price_history[0]
                    st.write(f"**Latest Price:** USD {latest_price['usd_clp']:,.0f} CLP | EUR {latest_price['eur_clp']:,.0f} CLP")
                    st.write(f"**Difference:** {latest_price['price_difference_clp']:+,.0f} CLP")
                    
                    if latest_price['is_good_opportunity']:
                        st.success("🟢 Currently a good opportunity!")
                    
                    st.write(f"**Price History:** {len(price_history)} records in last 30 days")
                else:
                    st.write("No price history available")
            
            with col2:
                if st.button(f"Remove", key=f"remove_{card['id']}"):
                    remove_card_from_watchlist(card['id'])
                    st.rerun()

def update_watchlist_prices(extraction_metadata: Dict):
    """Update prices for all cards in the watchlist."""
    watchlist_cards = get_watchlist_cards()
    
    if not watchlist_cards:
        return
    
    st.info(f"Updating prices for {len(watchlist_cards)} watchlist cards...")
    
    # This would be called during the extraction process to update
    # prices for cards that are already in the watchlist
    updated_count = 0
    
    for card in watchlist_cards:
        # Check if this card was in the current extraction results
        # and update its price data if found
        # This integration will be completed when connecting to the main app
        pass
    
    if updated_count > 0:
        st.success(f"Updated prices for {updated_count} watchlist cards")

def get_watchlist_summary() -> Dict:
    """Get a summary of the current watchlist."""
    watchlist_cards = get_watchlist_cards()
    
    if not watchlist_cards:
        return {
            'total_cards': 0,
            'good_opportunities': 0,
            'recent_additions': 0
        }
    
    # Count good opportunities (cards with recent good opportunity status)
    good_opportunities = 0
    for card in watchlist_cards:
        recent_prices = get_card_price_history(card['id'], days=7)
        if recent_prices and recent_prices[0]['is_good_opportunity']:
            good_opportunities += 1
    
    return {
        'total_cards': len(watchlist_cards),
        'good_opportunities': good_opportunities,
        'recent_additions': len([c for c in watchlist_cards if c['date_added'][:10] == pd.Timestamp.now().strftime('%Y-%m-%d')])
    }
