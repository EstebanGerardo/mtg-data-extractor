"""
Authentication module for MTG Arbitrage Tool
Provides secure user authentication and session management
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    """Manages user authentication for the MTG Arbitrage Tool"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the authentication manager"""
        try:
            self.config_path = Path(config_path)
            self.authenticator = None
            self.config = None
            self._load_config()
            self._setup_authenticator()
            logger.info("Authentication manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing authentication: {e}")
            raise
    
    def _load_config(self):
        """Load authentication configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.error(f"Authentication config file not found: {self.config_path}")
                st.error("Authentication configuration not found. Please contact administrator.")
                st.stop()
            
            with open(self.config_path, 'r') as file:
                self.config = yaml.load(file, Loader=SafeLoader)
                logger.info("Authentication configuration loaded successfully")
        
        except Exception as e:
            logger.error(f"Error loading authentication config: {e}")
            st.error("Error loading authentication configuration. Please contact administrator.")
            st.stop()
    
    def _setup_authenticator(self):
        """Setup the streamlit authenticator"""
        try:
            # Initialize the authenticator with auto_hash=True (default)
            # This will automatically hash plaintext passwords
            self.authenticator = stauth.Authenticate(
                self.config['credentials'],
                self.config['cookie']['name'],
                self.config['cookie']['key'],
                self.config['cookie']['expiry_days']
            )
            logger.info("Authenticator setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up authenticator: {e}")
            st.error(f"Error initializing authentication system: {e}")
            st.stop()
    
    def login(self):
        """Display login form and handle authentication"""
        try:
            # Use the correct login method for streamlit-authenticator v0.4.2
            login_result = self.authenticator.login()
            
            # Handle the case where login returns None
            if login_result is None:
                st.warning('Please enter your username and password')
                return False
            
            # Unpack the result if it's not None
            name, authentication_status, username = login_result
            
            if authentication_status == False:
                st.error('Username/password is incorrect')
                return False
            elif authentication_status == None:
                st.warning('Please enter your username and password')
                return False
            elif authentication_status:
                logger.info(f"User {username} logged in successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            st.error(f"Login error occurred: {e}")
            return False
    
    def logout(self):
        """Display logout button and handle logout"""
        try:
            self.authenticator.logout(location='sidebar')
        except Exception as e:
            logger.error(f"Error during logout: {e}")
    
    def get_user_info(self):
        """Get current user information"""
        return {
            'name': st.session_state.get('name'),
            'username': st.session_state.get('username'),
            'authentication_status': st.session_state.get('authentication_status')
        }
    
    def is_authenticated(self):
        """Check if user is currently authenticated"""
        return st.session_state.get('authentication_status') == True
    
    def require_auth(self):
        """Decorator-like function to require authentication"""
        if not self.is_authenticated():
            st.title("🎯 MTG Card Arbitrage Tool")
            st.markdown("---")
            st.markdown("### 🔐 Authentication Required")
            st.info("Please log in to access the MTG Card Arbitrage Tool.")
            
            # Display login form
            if not self.login():
                st.stop()
        
        return True

def create_auth_manager():
    """Factory function to create and return an AuthManager instance"""
    return AuthManager()

def hash_password(password: str) -> str:
    """Utility function to hash passwords for configuration"""
    return stauth.Hasher([password]).generate()[0]

if __name__ == "__main__":
    # Utility to generate password hashes
    passwords = ['admin123', 'user123']
    hashed_passwords = stauth.Hasher(passwords).generate()
    
    print("Password hashes for config.yaml:")
    for i, pwd in enumerate(['admin123', 'user123']):
        print(f"{pwd}: {hashed_passwords[i]}")
