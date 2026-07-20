import secrets
import urllib.parse

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
from config import (
    CLIENT_ID,
    SCOPES,
    AUTHORIZATION_ENDPOINT,
    get_redirect_uri,
)


# def login_google():
#     """
#     Redirect the user to Google's OAuth consent screen.
#     """

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

#     auth_url = (
#         AUTHORIZATION_ENDPOINT
#         + "?"
#         + urllib.parse.urlencode(params)
#     )

#     st.markdown(
#         f'<meta http-equiv="refresh" content="0;url={auth_url}">',
#         unsafe_allow_html=True,
#     )

def login_google():

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

    auth_url = (
        AUTHORIZATION_ENDPOINT
        + "?"
        + urllib.parse.urlencode(params)
    )

    st.write("DEBUG redirect_uri:", get_redirect_uri())
    st.write("DEBUG client_id:", CLIENT_ID)
    st.stop()  # <-- temporary, remove after debugging

#     st.markdown(
#     f'<meta http-equiv="refresh" content="0;url={auth_url}">',
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

def handle_callback():

    params = st.query_params

    code = params.get("code")
    state = params.get("state")

    if not code:
        return

    saved_state = st.session_state.get("oauth_state")

    # Validate only if the state survived
    if saved_state is not None and state != saved_state:
        st.error("OAuth state mismatch.")
        return

    try:

        token = exchange_code(code)


        st.session_state["oauth_token"] = token
        st.session_state["oauth_callback"] = True

        # Prevent callback from executing again
        st.query_params.clear()

        st.rerun()

    except Exception as e:

        st.exception(e)