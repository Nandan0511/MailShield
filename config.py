from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import os

load_dotenv()


def get_config(key, default=None):
    """
    Priority:
    1. Streamlit secrets (Cloud)
    2. Environment variables (.env)
    """

    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
# ---------------------------------------------------
# GOOGLE OAUTH
# ---------------------------------------------------
CLIENT_ID = get_config("GOOGLE_CLIENT_ID")
CLIENT_SECRET = get_config("GOOGLE_CLIENT_SECRET")

GOOGLE_REDIRECT_URI_LOCAL = get_config(
    "GOOGLE_REDIRECT_URI_LOCAL",
    "http://localhost:8501",
)

GOOGLE_REDIRECT_URI_CLOUD = get_config(
    "GOOGLE_REDIRECT_URI_CLOUD",
)

# SCOPES = [
#     "https://www.googleapis.com/auth/gmail.modify"
# ]
SCOPES = [
    "openid",
    "email",
    "profile"
]


def get_redirect_uri():
    if get_config("APP_ENV") == "cloud":
        return GOOGLE_REDIRECT_URI_CLOUD
    return GOOGLE_REDIRECT_URI_LOCAL
# ---------------------------------------------------
# TOKEN STORAGE
# ---------------------------------------------------
TOKEN_DIR = "tokens"


# ---------------------------------------------------
# SESSION + AUTO REFRESH
# ---------------------------------------------------
AUTO_REFRESH_MINUTES = 5

SESSION_TIMEOUT_MINUTES = 15


# ---------------------------------------------------
# SESSION DEFAULTS
# ---------------------------------------------------
SESSION_DEFAULTS = {

    # AUTH
    "logged_in": False,

    "email": "",

    "user_id": "",

    "service": None,

    "accounts": None,

    # EMAIL DATA
    "spam_emails": None,

    "ham_emails": None,

    "sender_count": None,

    "recipient_count": None,

    # FETCHING
    "fetch_on_login": False,

    "fetching_in_progress": False,

    "auto_fetch_in_progress": False,

    "force_fetch": False,

    "fetch_count": 0,

    "last_fetch_time": None,

    # MULTI ACCOUNT
    "multi_account_stats": None,

    "multi_stats_last_updated": None,

    "refresh_multi_stats": False,

    "show_multi_insights": False,

    "active_account_index": 0,

    # SESSION CONTROL
    "auto_login_checked": False,

    "show_login_prompt": False,

    "session_timed_out": False,

    "timeout_handled": False,

    "logout_triggered": False,

    "switching_account": False,

    "ui_refresh_needed": False,

    # USER ACTIVITY
    "last_active": datetime.now(),

    # SCAN SETTINGS
    "scan_days": 7,

    "email_limit": 50,

    "label_emails": True,

    "auto_scan_toggle": False
}
