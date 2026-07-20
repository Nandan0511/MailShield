# utils/cookies.py

import secrets
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# You can hardcode a password here or pull from st.secrets
cookies = EncryptedCookieManager(
    prefix="mailshield_",
    password=st.secrets["COOKIE_PASSWORD"],
)

def get_device_id():
    """
    Returns a stable random ID for this browser.
    Creates and saves one if it doesn't exist yet.
    """

    if not cookies.ready():
        return None

    device_id = cookies.get("device_id")

    if not device_id:
        device_id = secrets.token_urlsafe(24)
        cookies["device_id"] = device_id
        cookies.save()

    return device_id