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
import bcrypt

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
            # Simplified login page design with purple theme
            st.markdown("""
            <style>
            .login-header {
                background: linear-gradient(90deg, #581c87 0%, #8b5cf6 100%);
                padding: 3rem 2rem;
                border-radius: 12px;
                margin-bottom: 3rem;
                color: white;
                text-align: center;
            }
            .login-header h1 {
                margin: 0;
                font-size: 3rem;
                font-weight: 600;
                letter-spacing: -0.025em;
            }
            .login-header p {
                margin: 1rem 0 0 0;
                font-size: 1.2rem;
                opacity: 0.9;
            }
            /* Purple accent for form buttons */
            .stButton > button {
                background: linear-gradient(90deg, #581c87 0%, #8b5cf6 100%) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
            }
            .stButton > button:hover {
                background: linear-gradient(90deg, #4c1d95 0%, #7c3aed 100%) !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3) !important;
            }
            /* Center the login button */
            .stButton {
                display: flex !important;
                justify-content: center !important;
                margin-top: 1rem !important;
            }
            /* Purple accent for input fields */
            .stTextInput > div > div > input {
                border-color: #8b5cf6 !important;
                border-width: 2px !important;
            }
            .stTextInput > div > div > input:focus {
                border-color: #581c87 !important;
                box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important;
                outline: none !important;
            }
            /* Purple accent for input labels */
            .stTextInput > label {
                color: #8b5cf6 !important;
                font-weight: 600 !important;
            }
            /* Form styling with purple theme (primary color handled by config.toml) */
            div[data-testid="stForm"] {
                border-radius: 12px !important;
            }
            /* Center form with limited width */
            .login-form {
                max-width: 400px;
                margin: 0 auto;
                padding: 0 20px;
            }
            /* Override Streamlit's default form width */
            .login-form .stTextInput > div > div > input {
                max-width: 100% !important;
            }
            .login-form .stForm {
                max-width: 400px !important;
                margin: 0 auto !important;
            }
            /* Make the form container narrower */
            div[data-testid="stForm"] {
                max-width: 400px !important;
                margin: 0 auto !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Simplified login header
            st.markdown("""
            <div class="login-header">
                <h1>■ MTG Singles</h1>
                <p>Card Management System</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a simple login form using Streamlit columns for centering
            col1, col2, col3 = st.columns([1, 2, 1])  # Center column is twice as wide
            
            with col2:  # Use the center column
                with st.form("login_form"):
                    username_input = st.text_input("▦ Username", placeholder="Enter your username")
                    password_input = st.text_input("▦ Password", type="password", placeholder="Enter your password")
                    login_button = st.form_submit_button("Login")
                
                if login_button:
                    if username_input and password_input:
                        # Debug: Show what we're checking
                        logger.info(f"Login attempt - Username: {username_input}, Password length: {len(password_input)}")
                        logger.info(f"Available usernames: {list(self.config['credentials']['usernames'].keys())}")
                        
                        # Check credentials against config
                        if username_input in self.config['credentials']['usernames']:
                            user_data = self.config['credentials']['usernames'][username_input]
                            stored_password = user_data['password']
                            
                            logger.info(f"Stored password for {username_input}: {stored_password}")
                            logger.info(f"Input password: {password_input}")
                            
                            # Check if password is bcrypt hashed (starts with $2b$)
                            if stored_password.startswith('$2b$'):
                                # Verify bcrypt hashed password
                                password_match = bcrypt.checkpw(password_input.encode('utf-8'), stored_password.encode('utf-8'))
                                logger.info(f"Bcrypt password match: {password_match}")
                            else:
                                # For plaintext passwords, compare directly
                                password_match = password_input == stored_password
                                logger.info(f"Plaintext password match: {password_match}")
                            
                            if password_match:
                                # Set session state for successful login
                                st.session_state['authentication_status'] = True
                                st.session_state['name'] = user_data['name']
                                st.session_state['username'] = username_input
                                
                                logger.info(f"User {username_input} logged in successfully")
                                st.success(f'■ Welcome {user_data["name"]}!')
                                st.rerun()
                            else:
                                st.error('■ Username/password is incorrect')
                                logger.warning(f"Password mismatch for user {username_input}")
                        else:
                            st.error('■ Username/password is incorrect')
                            logger.warning(f"Username {username_input} not found in config")
                    else:
                        st.warning('○ Please enter both username and password')
            
            # If we reach here, user hasn't logged in yet
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
