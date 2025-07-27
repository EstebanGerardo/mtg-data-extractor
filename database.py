"""
Database module for MTG Card Watchlist functionality.
Handles SQLite database operations for tracking selected cards over time.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'watchlist.db')

def ensure_data_directory():
    """Ensure the data directory exists."""
    data_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logging.info(f"Created data directory: {data_dir}")

def init_database():
    """Initialize the database with required tables."""
    ensure_data_directory()
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Create watchlist_cards table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create price_tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER NOT NULL,
                    tracked_date TIMESTAMP NOT NULL,
                    usd_price REAL,
                    eur_price REAL,
                    usd_clp REAL,
                    eur_clp REAL,
                    price_difference_clp REAL,
                    usd_to_clp_rate REAL,
                    eur_to_clp_rate REAL,
                    is_good_opportunity BOOLEAN DEFAULT FALSE,
                    clp_threshold_used REAL,
                    deck_count INTEGER,
                    deck_percentage REAL,
                    FOREIGN KEY (card_id) REFERENCES watchlist_cards (id),
                    UNIQUE(card_id, tracked_date)
                )
            ''')
            
            # Create extraction_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extraction_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    time_period TEXT NOT NULL,
                    num_cards_extracted INTEGER,
                    num_cards_with_prices INTEGER,
                    num_cards_selected INTEGER,
                    clp_threshold REAL
                )
            ''')
            
            # Create selection_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS selection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    card_name TEXT NOT NULL,
                    was_selected BOOLEAN DEFAULT FALSE,
                    usd_price REAL,
                    eur_price REAL,
                    price_difference_clp REAL,
                    is_good_opportunity BOOLEAN,
                    FOREIGN KEY (session_id) REFERENCES extraction_sessions (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_name ON watchlist_cards (name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_tracking_card_date ON price_tracking (card_id, tracked_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_selection_history_session ON selection_history (session_id)')
            
            conn.commit()
            logging.info("Database initialized successfully")
            
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
        raise

def save_extraction_session(time_period: str, num_cards_extracted: int, 
                           num_cards_with_prices: int, clp_threshold: float) -> int:
    """Save extraction session metadata and return session ID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO extraction_sessions 
                (time_period, num_cards_extracted, num_cards_with_prices, clp_threshold)
                VALUES (?, ?, ?, ?)
            ''', (time_period, num_cards_extracted, num_cards_with_prices, clp_threshold))
            
            session_id = cursor.lastrowid
            conn.commit()
            logging.info(f"Saved extraction session {session_id}")
            return session_id
            
    except sqlite3.Error as e:
        logging.error(f"Error saving extraction session: {e}")
        raise

def add_card_to_watchlist(card_name: str, notes: str = "") -> int:
    """Add a card to the watchlist. Returns card ID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Try to insert new card
            cursor.execute('''
                INSERT OR IGNORE INTO watchlist_cards (name, notes)
                VALUES (?, ?)
            ''', (card_name, notes))
            
            # Get the card ID (either newly inserted or existing)
            cursor.execute('SELECT id FROM watchlist_cards WHERE name = ?', (card_name,))
            card_id = cursor.fetchone()[0]
            
            # If notes provided and card already existed, update notes
            if notes and cursor.rowcount == 0:
                cursor.execute('''
                    UPDATE watchlist_cards SET notes = ?, is_active = TRUE 
                    WHERE id = ?
                ''', (notes, card_id))
            
            conn.commit()
            logging.info(f"Added/updated card '{card_name}' in watchlist (ID: {card_id})")
            return card_id
            
    except sqlite3.Error as e:
        logging.error(f"Error adding card to watchlist: {e}")
        raise

def save_price_data(card_id: int, price_data: Dict) -> bool:
    """Save price tracking data for a card."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Check if data for this card and date already exists
            today = datetime.now().date()
            cursor.execute('''
                SELECT id FROM price_tracking 
                WHERE card_id = ? AND DATE(tracked_date) = ?
            ''', (card_id, today))
            
            if cursor.fetchone():
                # Update existing record
                cursor.execute('''
                    UPDATE price_tracking SET
                        usd_price = ?, eur_price = ?, usd_clp = ?, eur_clp = ?,
                        price_difference_clp = ?, usd_to_clp_rate = ?, eur_to_clp_rate = ?,
                        is_good_opportunity = ?, clp_threshold_used = ?,
                        deck_count = ?, deck_percentage = ?
                    WHERE card_id = ? AND DATE(tracked_date) = ?
                ''', (
                    price_data.get('usd_price'), price_data.get('eur_price'),
                    price_data.get('usd_clp'), price_data.get('eur_clp'),
                    price_data.get('price_difference_clp'), price_data.get('usd_to_clp_rate'),
                    price_data.get('eur_to_clp_rate'), price_data.get('is_good_opportunity'),
                    price_data.get('clp_threshold_used'), price_data.get('deck_count'),
                    price_data.get('deck_percentage'), card_id, today
                ))
                logging.info(f"Updated price data for card ID {card_id}")
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO price_tracking 
                    (card_id, tracked_date, usd_price, eur_price, usd_clp, eur_clp,
                     price_difference_clp, usd_to_clp_rate, eur_to_clp_rate,
                     is_good_opportunity, clp_threshold_used, deck_count, deck_percentage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    card_id, datetime.now(), price_data.get('usd_price'),
                    price_data.get('eur_price'), price_data.get('usd_clp'),
                    price_data.get('eur_clp'), price_data.get('price_difference_clp'),
                    price_data.get('usd_to_clp_rate'), price_data.get('eur_to_clp_rate'),
                    price_data.get('is_good_opportunity'), price_data.get('clp_threshold_used'),
                    price_data.get('deck_count'), price_data.get('deck_percentage')
                ))
                logging.info(f"Inserted new price data for card ID {card_id}")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        logging.error(f"Error saving price data: {e}")
        return False

def get_watchlist_cards() -> List[Dict]:
    """Get all active cards in the watchlist."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, date_added, notes, is_active
                FROM watchlist_cards
                WHERE is_active = TRUE
                ORDER BY date_added DESC
            ''')
            
            columns = ['id', 'name', 'date_added', 'notes', 'is_active']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
    except sqlite3.Error as e:
        logging.error(f"Error getting watchlist cards: {e}")
        return []

def get_card_price_history(card_id: int, days: int = 30) -> List[Dict]:
    """Get price history for a specific card."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tracked_date, usd_price, eur_price, usd_clp, eur_clp,
                       price_difference_clp, is_good_opportunity, deck_count, deck_percentage
                FROM price_tracking
                WHERE card_id = ? AND tracked_date >= datetime('now', '-{} days')
                ORDER BY tracked_date DESC
            '''.format(days), (card_id,))
            
            columns = ['tracked_date', 'usd_price', 'eur_price', 'usd_clp', 'eur_clp',
                      'price_difference_clp', 'is_good_opportunity', 'deck_count', 'deck_percentage']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
    except sqlite3.Error as e:
        logging.error(f"Error getting card price history: {e}")
        return []

def update_extraction_session_selections(session_id: int, num_cards_selected: int):
    """Update the number of cards selected for a session."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE extraction_sessions 
                SET num_cards_selected = ?
                WHERE id = ?
            ''', (num_cards_selected, session_id))
            conn.commit()
            logging.info(f"Updated session {session_id} with {num_cards_selected} selected cards")
            
    except sqlite3.Error as e:
        logging.error(f"Error updating extraction session: {e}")

def save_selection_history(session_id: int, cards_data: List[Dict]):
    """Save the selection history for an extraction session."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            for card in cards_data:
                cursor.execute('''
                    INSERT INTO selection_history 
                    (session_id, card_name, was_selected, usd_price, eur_price,
                     price_difference_clp, is_good_opportunity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, card.get('card_name'), card.get('was_selected', False),
                    card.get('usd_price'), card.get('eur_price'),
                    card.get('price_difference_clp'), card.get('is_good_opportunity', False)
                ))
            
            conn.commit()
            logging.info(f"Saved selection history for session {session_id}")
            
    except sqlite3.Error as e:
        logging.error(f"Error saving selection history: {e}")

def remove_card_from_watchlist(card_id: int):
    """Remove a card from the watchlist (set as inactive)."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE watchlist_cards 
                SET is_active = FALSE
                WHERE id = ?
            ''', (card_id,))
            conn.commit()
            logging.info(f"Removed card ID {card_id} from watchlist")
            
    except sqlite3.Error as e:
        logging.error(f"Error removing card from watchlist: {e}")

def get_database_stats() -> Dict:
    """Get database statistics."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Count watchlist cards
            cursor.execute('SELECT COUNT(*) FROM watchlist_cards WHERE is_active = TRUE')
            active_cards = cursor.fetchone()[0]
            
            # Count total price records
            cursor.execute('SELECT COUNT(*) FROM price_tracking')
            price_records = cursor.fetchone()[0]
            
            # Count extraction sessions
            cursor.execute('SELECT COUNT(*) FROM extraction_sessions')
            sessions = cursor.fetchone()[0]
            
            return {
                'active_watchlist_cards': active_cards,
                'total_price_records': price_records,
                'extraction_sessions': sessions
            }
            
    except sqlite3.Error as e:
        logging.error(f"Error getting database stats: {e}")
        return {}
