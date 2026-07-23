# import secrets
# import urllib.parse
# import streamlit.components.v1 as components
# import streamlit as st
# import requests

# from config import (
#     CLIENT_ID,
#     CLIENT_SECRET,
#     SCOPES,
#     AUTHORIZATION_ENDPOINT,
#     TOKEN_ENDPOINT,
#     get_redirect_uri,
#     get_config,
# )

# def login_google():
#     state = secrets.token_urlsafe(32)
#     st.session_state["oauth_state"] = state

#     params = {
#         "client_id": CLIENT_ID,
#         "redirect_uri": get_redirect_uri(),
#         "response_type": "code",
#         "scope": " ".join(SCOPES),
#         "access_type": "offline",
#         "prompt": "consent",
#         "include_granted_scopes": "true",
#         "state": state,
#     }

#     auth_url = AUTHORIZATION_ENDPOINT + "?" + urllib.parse.urlencode(params)

#     return auth_url

# def exchange_code(code):

#     response = requests.post(
#         TOKEN_ENDPOINT,
#         data={
#             "client_id": CLIENT_ID,
#             "client_secret": CLIENT_SECRET,
#             "code": code,
#             "grant_type": "authorization_code",
#             "redirect_uri": get_redirect_uri(),
#         },
#     )

#     print("Status:", response.status_code)
#     print("Response:", response.text)

#     response.raise_for_status()

#     return response.json()
# # ---------------------------------------------------
# # GLOBAL IDEMPOTENCY GUARD (shared across all sessions)
# # Prevents the same authorization code from ever being
# # exchanged twice, even if multiple browser
# # sessions/reruns see it (prefetch, reconnect, etc).
# # ---------------------------------------------------
# _used_codes = set()

# def handle_callback():

#     params = st.query_params

#     code = params.get("code")
#     state = params.get("state")

#     if not code:
#         return

#     if code in _used_codes:
#         st.query_params.clear()
#         return

#     _used_codes.add(code)

#     saved_state = st.session_state.get("oauth_state")

#     try:

#         if saved_state is not None and state != saved_state:
#             st.error("OAuth state mismatch.")
#             return

#         token = exchange_code(code)

#         st.session_state["oauth_token"] = token
#         st.session_state["oauth_callback"] = True

#     except Exception as e:

#         st.exception(e)

#     finally:

#         st.query_params.clear()
#         st.rerun()

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
)


def login_google():
    """
    Builds the Google OAuth authorization URL. Does NOT render
    anything — the caller (sidebar.py) is responsible for showing
    a button/link that opens this URL in a popup window named
    'mailshield_oauth'.
    """
    state = secrets.token_urlsafe(32)
    st.session_state["oauth_state"] = state

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

    return auth_url


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
    if response.status_code != 200:
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
            st.stop()

        token = exchange_code(code)

        st.session_state["oauth_token"] = token
        st.session_state["oauth_callback"] = True

        st.query_params.clear()

        # -----------------------------------------------
        # Actually save the token to disk NOW, since this
        # popup tab stops right after — main.py's later
        # authenticate_gmail() call would never run otherwise.
        # -----------------------------------------------
        from auth import authenticate_gmail
        authenticate_gmail()

        st.success("✅ Account connected successfully!")
        st.caption("This window will close automatically. If it doesn't, you can close it yourself.")

        components.html(
            """
            <script>
            (function() {
                if (window.top.name === 'mailshield_oauth') {
                    localStorage.setItem('mailshield_login_done', Date.now().toString());
                }
                setTimeout(function() {
                    try { window.top.close(); } catch (e) {}
                }, 1200);
            })();
            </script>
            """,
            height=0,
        )

        st.stop()

    except Exception as e:

        st.exception(e)
        st.query_params.clear()
        st.stop()