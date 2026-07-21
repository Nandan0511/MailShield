import secrets
import urllib.parse
import streamlit.components.v1 as components
import streamlit as st
import requests

from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    SCOPES,
    AUTHORIZATION_ENDPOINT,
    TOKEN_ENDPOINT,
    get_redirect_uri,
    get_config,
)

def login_google():
    state = secrets.token_urlsafe(32)
    st.session_state["oauth_state"] = state
    
    st.write("APP_ENV =", get_config("APP_ENV"))
    st.write("CLIENT_ID:", CLIENT_ID)
    st.write("REDIRECT_URI:", get_redirect_uri())
    st.write("SCOPES:", SCOPES)
    st.write("SCOPES USED:", SCOPES)

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }

    auth_url = AUTHORIZATION_ENDPOINT + "?" + urllib.parse.urlencode(params)
    st.code(auth_url)

    components.html(
    f"""
    <button
        style="
            width:100%;
            padding:10px;
            border-radius:8px;
            cursor:pointer;
        "
        onclick="window.location.href='{auth_url}'">
        🔐 Connect Gmail
    </button>
    """,
    height=60,
)

    # st.link_button("🔐 Connect Gmail", auth_url, use_container_width=True)
#     st.markdown(
#     f"""
#     <a href="{auth_url}" target="_top" style="
#         display: inline-block;
#         width: 100%;
#         text-align: center;
#         padding: 0.5rem 1rem;
#         background-color: rgb(19, 23, 32);
#         color: white;
#         border: 1px solid rgba(250, 250, 250, 0.2);
#         border-radius: 8px;
#         text-decoration: none;
#         font-weight: 500;
#     ">
#         🔐 Connect Gmail
#     </a>
#     """,
#     unsafe_allow_html=True,
# )

def exchange_code(code):

    response = requests.post(
        TOKEN_ENDPOINT,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": get_redirect_uri(),
        },
    )

    print("Status:", response.status_code)
    print("Response:", response.text)

    response.raise_for_status()

    return response.json()
# ---------------------------------------------------
# GLOBAL IDEMPOTENCY GUARD (shared across all sessions)
# Prevents the same authorization code from ever being
# exchanged twice, even if multiple browser
# sessions/reruns see it (prefetch, reconnect, etc).
# ---------------------------------------------------
_used_codes = set()


def handle_callback():

    params = st.query_params

    code = params.get("code")
    state = params.get("state")

    if not code:
        return

    if code in _used_codes:
        st.query_params.clear()
        return

    _used_codes.add(code)

    saved_state = st.session_state.get("oauth_state")

    try:

        if saved_state is not None and state != saved_state:
            st.error("OAuth state mismatch.")
            return

        token = exchange_code(code)

        st.session_state["oauth_token"] = token
        st.session_state["oauth_callback"] = True

    except Exception as e:

        st.exception(e)

    finally:

        st.query_params.clear()
        st.rerun()