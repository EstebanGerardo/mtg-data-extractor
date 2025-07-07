import streamlit as st
import pandas as pd
import logging
import subprocess
import json
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
MAX_SELLERS_TO_CHECK = 15 # This is now for display purposes, actual value is in scraper.py

# --- Main Function ---

def find_best_offer(card_name):
    """
    Calls the scraper.py script as a subprocess to find the best offer.
    This avoids asyncio event loop conflicts with Streamlit.
    """
    # Ensure we are using the python executable from the virtual environment
    python_executable = sys.executable
    
    command = [python_executable, "scraper.py", card_name]
    
    try:
        logging.info(f"Running command: {' '.join(command)}")
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True, # Raises CalledProcessError for non-zero exit codes
            encoding='utf-8'
        )
        
        logging.info(f"Scraper stdout: {process.stdout}")
        # The last line of stdout should be our JSON result
        last_line = process.stdout.strip().split('\n')[-1]
        result = json.loads(last_line)

        if result.get("error"):
            return result["error"]
        return result

    except subprocess.CalledProcessError as e:
        logging.error(f"Scraper script failed with exit code {e.returncode}")
        logging.error(f"Stderr: {e.stderr}")
        return f"The scraper script failed. Check logs for details. Stderr: {e.stderr}"
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from scraper: {e}")
        return "The scraper script returned invalid data."
    except Exception as e:
        logging.error("An unexpected error occurred while running the scraper", exc_info=True)
        return f"An unexpected error occurred: {e}"


# --- Streamlit UI ---
st.title("Automated Cardmarket Seller Finder")
st.markdown("**Phase 1: Single Card MVP**")
st.write("Enter a Magic: The Gathering card name to find the seller with the lowest total price (card + shipping) to Spain.")

card_name_input = st.text_input("Enter Card Name:", placeholder="e.g., Sol Ring, Æther Vial")

if st.button("Find Best Deal"):
    if card_name_input:
        with st.spinner('Querying Cardmarket... this may take a moment.'):
            result = find_best_offer(card_name_input)

        st.markdown("---_---") # Separator

        if isinstance(result, dict):
            st.success("**Found the best offer!**")
            st.markdown(f"**Seller:** `{result['seller']}`")
            st.markdown(f"**Card Price:** `{result['card_price']:.2f} €`")
            st.markdown(f"**Shipping Price:** `{result['shipping_price']:.2f} €`")
            st.markdown(f"### **Total Price: `{result['total_price']:.2f} €`**")
            st.markdown(f"<a href='{result['link']}' target='_blank'>Go to Seller's Offer Page</a>", unsafe_allow_html=True)
        else:
            st.error(result)
    else:
        st.warning("Please enter a card name.")

st.sidebar.header("Project Info")
st.sidebar.info(
    "This app automates finding the best deal on Cardmarket for a single card shipped to Spain."
    "It is based on the requirements from the PRD."
)
st.sidebar.header("Scope Limitations (MVP)")
st.sidebar.warning(
    f"- Single card only\n"
    f"- No filters (condition, language, etc.)\n"
    f"- Only Professional & Power Sellers\n"
    f"- Assumes shipping to Barcelona, Spain\n"
    f"- Checks top {MAX_SELLERS_TO_CHECK} sellers for performance"
)
