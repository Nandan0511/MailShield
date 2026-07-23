# # utils/cookies.py

# import secrets
# import streamlit as st
# from streamlit_cookies_manager import EncryptedCookieManager

# # You can hardcode a password here or pull from st.secrets
# cookies = EncryptedCookieManager(
#     prefix="mailshield_",
#     password=st.secrets["COOKIE_PASSWORD"],
# )

# def get_device_id():
#     """
#     Returns a stable random ID for this browser.
#     Creates and saves one if it doesn't exist yet.
#     """

#     if not cookies.ready():
#         return None

#     device_id = cookies.get("device_id")

#     if not device_id:
#         device_id = secrets.token_urlsafe(24)
#         cookies["device_id"] = device_id
#         cookies.save()

#     return device_id
# utils/cookies.py

import streamlit as st
import extra_streamlit_components as stx
import secrets
import streamlit.components.v1 as components

def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state["cookie_manager"] = stx.CookieManager()
    return st.session_state["cookie_manager"]


def get_device_id():
    """
    Returns a stable device ID that survives full page
    reloads/navigations (like the OAuth redirect round trip),
    unlike st.session_state which resets on those.

    Uses st.context.cookies (read-only, reflects the browser's
    real cookies) + a one-line JS snippet to set the cookie the
    first time. No custom bidirectional component involved, so
    it avoids the reconnect/rerun issues we hit before.
    """

    existing = st.context.cookies.get("mailshield_device_id")
    st.write("DEBUG existing cookie:", existing)

    if existing:
        return existing

    # No cookie yet on this request — generate one, remember it
    # for THIS run in session_state, and write it to the browser
    # via JS so it's present on the NEXT real request (including
    # after the OAuth redirect round trip).
    if "device_id" not in st.session_state:
        st.session_state["device_id"] = secrets.token_urlsafe(24)

    device_id = st.session_state["device_id"]

    components.html(
        f"""
        <script>
        document.cookie = "mailshield_device_id={device_id}; path=/; max-age=31536000; SameSite=Lax ;Secure";
        </script>
        """,
        height=0,
        width=0,
    )

    return device_id

# def get_device_id():
#     if "device_id" not in st.session_state:
#         st.session_state["device_id"] = secrets.token_urlsafe(24)
#     return st.session_state["device_id"]