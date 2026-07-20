import os
import json
import requests
import streamlit as st

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


from config import (
    SCOPES,
    CLIENT_ID,
    CLIENT_SECRET,
    AUTHORIZATION_ENDPOINT,
    TOKEN_ENDPOINT,
    get_redirect_uri,
)

from utils.token_utils import (
    get_token_path,
    clean_duplicate_tokens_safe,
)

from utils.session import (
    initialize_session_state,
)

initialize_session_state()

# ---------------------------------------------------
# BUILD CREDENTIALS FROM AN OAUTH TOKEN DICT
# ---------------------------------------------------
def create_google_credentials(token):

    if not token:
        return None

    return Credentials(
        token=token.get("access_token"),
        refresh_token=token.get("refresh_token"),
        token_uri=TOKEN_ENDPOINT,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
    )


# ---------------------------------------------------
# BUILD GMAIL SERVICE FROM CREDENTIALS
# ---------------------------------------------------
def build_gmail_service(creds):

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )


# ---------------------------------------------------
# SAVE / LOAD TOKEN ON DISK
# ---------------------------------------------------
# def save_token(email, creds):

#     token_path = get_token_path(email)

#     os.makedirs(
#         os.path.dirname(token_path),
#         exist_ok=True,
#     )

#     with open(token_path, "w") as token_file:

#         token_file.write(creds.to_json())

#     clean_duplicate_tokens_safe()


# def load_saved_token(email):

#     token_path = get_token_path(email)

#     if not os.path.exists(token_path):
#         return None

#     return Credentials.from_authorized_user_file(
#         token_path,
#         SCOPES,
#     )


def save_token(device_id, email, creds):
    token_path = get_token_path(device_id, email)
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w") as f:
        f.write(creds.to_json())

def load_saved_token(device_id, email):
    token_path = get_token_path(device_id, email)
    if not os.path.exists(token_path):
        return None
    return Credentials.from_authorized_user_file(token_path, SCOPES)

def refresh_saved_token(creds):

    if creds and creds.expired and creds.refresh_token:

        creds.refresh(Request())

    return creds


# ---------------------------------------------------
# AUTHENTICATE GMAIL (step 2 of the flow)
# ---------------------------------------------------
def authenticate_gmail():
    """
    Called once the OAuth token exists in session state
    (either freshly granted via login_button(), or loaded
    from a saved token.json for the active/auto-login
    account). Builds Credentials, builds the Gmail service,
    fetches the profile, and populates session state.
    """

    try:

        creds = None

        # -------------------------------------------
        # PREFER A FRESH TOKEN FROM login_button()
        # -------------------------------------------
        raw_token = st.session_state.get("oauth_token")

        if raw_token:

            creds = create_google_credentials(raw_token)

        # -------------------------------------------
        # OTHERWISE FALL BACK TO A SAVED TOKEN FILE
        # -------------------------------------------
        if not creds:

            device_id = st.session_state.get("device_id")
            active_email = st.session_state.get("email", "")
            creds = load_saved_token(device_id , active_email)

        if not creds:

            st.error("❌ No credentials available. Please log in.")

            return None

        # -------------------------------------------
        # REFRESH IF NEEDED
        # -------------------------------------------
        if not creds.valid:

            try:

                creds = refresh_saved_token(creds)

            except Exception:

                st.error("❌ Session expired. Please log in again.")

                clear_session()

                return None

        # -------------------------------------------
        # BUILD GMAIL SERVICE
        # -------------------------------------------
        service = build_gmail_service(creds)

        # -------------------------------------------
        # FETCH PROFILE
        # -------------------------------------------
        profile = (
            service.users()
            .getProfile(userId="me")
            .execute()
        )

        email = profile.get("emailAddress", "")

        if not email:

            st.error("❌ Could not retrieve Gmail address.")

            return None

        # -------------------------------------------
        # SAVE TOKEN
        # -------------------------------------------
        device_id = st.session_state.get("device_id")
        save_token(device_id,email, creds)

        # -------------------------------------------
        # UPDATE ACCOUNTS
        # -------------------------------------------
        if email not in st.session_state.accounts:

            st.session_state.accounts.append(email)

        # -------------------------------------------
        # SESSION STATE
        # -------------------------------------------
        st.session_state.email = email

        st.session_state.user_id = (
            email.split("@")[0].capitalize()
        )

        st.session_state.logged_in = True

        st.session_state.service = service

        st.session_state.fetch_on_login = True

        st.session_state.fetching_in_progress = False

        st.session_state.force_fetch = False

        st.session_state.logout_triggered = False

        st.session_state.switching_account = False

        st.session_state.auto_login_checked = False

        st.session_state.last_active = None

        # keep the raw token around for refresh_token()/revoke_token()
        st.session_state.oauth_token = json.loads(creds.to_json())

        st.toast(f"✅ Connected: {email}")

        return service

    except Exception as e:

        st.error(f"❌ Authentication Error: {e}")

        return None


# ---------------------------------------------------
# GET GMAIL SERVICE
# ---------------------------------------------------
def get_gmail_service(email=""):

    return authenticate_gmail()


# ---------------------------------------------------
# LOAD EXISTING ACCOUNT SERVICE
# ---------------------------------------------------
def load_account_service(email):
    try:
        device_id = st.session_state.get("device_id")
        creds = load_saved_token(device_id, email)

        if not creds:
            st.error("❌ Token not found.")
            return None

        creds = refresh_saved_token(creds)
        service = build_gmail_service(creds)
        return service

    except Exception as e:
        st.error(f"❌ Failed loading account: {e}")
        return None

# ---------------------------------------------------
# AUTO LOGIN
# ---------------------------------------------------
# AFTER
def auto_login():
    if (
        not st.session_state.get("logged_in", False)
        and not st.session_state.get("auto_login_checked", False)
        and st.session_state.get("accounts", [])
    ):
        device_id = st.session_state.get("device_id")

        for saved_email in st.session_state.accounts:
            try:
                creds = load_saved_token(device_id, saved_email)
                if not creds:
                    continue

                if creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception:
                        continue

                if creds.valid:
                    save_token(device_id, saved_email, creds)
                    service = build_gmail_service(creds)

                    st.session_state.email = saved_email
                    st.session_state.user_id = saved_email.split("@")[0].capitalize()
                    st.session_state.service = service
                    st.session_state.oauth_token = json.loads(creds.to_json())
                    st.session_state.logged_in = True
                    st.session_state.fetch_on_login = True

                    st.toast(f"✅ Auto-logged in as {saved_email}")
                    break

            except Exception:
                continue

        st.session_state.auto_login_checked = True
# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------
def logout(remember_me=True):
    """
    Revokes the current OAuth token via streamlit-oauth's
    revoke endpoint, then clears session state. If
    remember_me is False, also deletes the saved token.json
    so the user is required to log in again next visit.
    """

    token = st.session_state.get("oauth_token")

    if token:

        try:
            requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={
                "token": token.get("access_token")
            },
            headers={
                "content-type":
                "application/x-www-form-urlencoded"
            },
        )

           

        except Exception:
            # Revocation failing shouldn't block logout locally
            pass

    if not remember_me:

        device_id = st.session_state.get("device_id")
        current_email = st.session_state.get("email", "")
        token_path = get_token_path(device_id,current_email)

        if os.path.exists(token_path):

            os.remove(token_path)

        if current_email in st.session_state.get("accounts", []):

            st.session_state.accounts.remove(current_email)

    if "oauth_token" in st.session_state:

        del st.session_state["oauth_token"]

    clear_session()


# ---------------------------------------------------
# CLEAR SESSION
# ---------------------------------------------------
def clear_session(keys=None):

    if keys is None:

        keys = [
            "logged_in",
            "email",
            "user_id",
            "service",
            "spam_emails",
            "ham_emails",
            "sender_count",
            "recipient_count",
            "fetch_on_login",
            "fetching_in_progress",
            "force_fetch",
            "show_login_prompt",
        ]

    # -----------------------------------------------
    # REMOVE KEYS
    # -----------------------------------------------
    for key in keys:

        if key in st.session_state:

            del st.session_state[key]

    # -----------------------------------------------
    # ALWAYS PURGE THE OAUTH TOKEN
    # (otherwise a leftover token in session state gets
    # picked back up by the "complete OAuth login" check
    # in main_app.py and silently re-authenticates)
    # -----------------------------------------------
    if "oauth_token" in st.session_state:

        del st.session_state["oauth_token"]

    # -----------------------------------------------
    # SAFE RESETS
    # -----------------------------------------------
    st.session_state.logged_in = False

    st.session_state.service = None

    st.session_state.fetch_on_login = False

    st.session_state.fetching_in_progress = False

    st.session_state.force_fetch = False

    st.session_state.logout_triggered = True

    st.session_state.switching_account = False

    st.session_state.auto_login_checked = False

    st.session_state.spam_emails = []

    st.session_state.ham_emails = []

    st.session_state.sender_count = {}

    st.session_state.recipient_count = {}

    st.session_state.last_fetch_time = None
# import os
# import json

# import streamlit as st

# from google.oauth2.credentials import Credentials
# from google.auth.transport.requests import Request
# from googleapiclient.discovery import build

# from streamlit_oauth import OAuth2Component

# from config import (
#     SCOPES,
#     CLIENT_ID,
#     CLIENT_SECRET,
#     AUTHORIZATION_ENDPOINT,
#     TOKEN_ENDPOINT,
#     REDIRECT_URI,
# )

# from utils.token_utils import (
#     get_token_path,
#     clean_duplicate_tokens_safe,
# )

# from utils.session import (
#     initialize_session_state,
# )

# initialize_session_state()

# # ---------------------------------------------------
# # OAUTH2 COMPONENT (web flow, Streamlit Cloud safe)
# # ---------------------------------------------------
# _oauth2 = OAuth2Component(
#     client_id=CLIENT_ID,
#     client_secret=CLIENT_SECRET,
#     authorize_endpoint=AUTHORIZATION_ENDPOINT,
#     token_endpoint=TOKEN_ENDPOINT,
#     refresh_token_endpoint=TOKEN_ENDPOINT,
#     revoke_token_endpoint="https://oauth2.googleapis.com/revoke",
# )


# # ---------------------------------------------------
# # LOGIN BUTTON (step 1 of the two-step OAuth flow)
# # ---------------------------------------------------
# def login_button(
#     name="🔗 Connect First Gmail Account",
#     icon="https://www.google.com/favicon.ico",
#     key="google_oauth",
#     caption="Sign in to connect your Gmail account",
#     card_key=None,
# ):
#     """
#     Renders the Google sign-in button inside a themed card
#     (label/icon/key/caption are customizable so this can be
#     reused anywhere — sidebar, main area, "add another
#     account", etc.). The card is a keyed st.container, so
#     callers can target it with CSS via the `.st-key-<card_key>`
#     class (defaults to `login_card_<key>`). The Google button
#     itself renders in a sandboxed iframe with fixed styling
#     (per Google's own brand guidelines it isn't meant to be
#     recolored) — the card around it is what we style.

#     On success, stores the raw OAuth token dict in
#     st.session_state.oauth_token and triggers a rerun.
#     Call this instead of authenticate_gmail() when the
#     user is not yet logged in (see main_app.py / sidebar.py).
#     """

#     card_key = card_key or f"login_card_{key}"

#     with st.container(border=True, key=card_key):

#         if caption:

#             st.caption(caption)

#         result = _oauth2.authorize_button(
#             name=name,
#             icon=icon,
#             redirect_uri=REDIRECT_URI,
#             scope=" ".join(SCOPES),
#             key=key,
#             extras_params={
#                 "access_type": "offline",
#                 "prompt": "consent",
#             },
#             use_container_width=True,
#         )

#     if result and "token" in result:

#         st.session_state.oauth_token = result["token"]

#         st.rerun()


# # ---------------------------------------------------
# # BUILD CREDENTIALS FROM AN OAUTH TOKEN DICT
# # ---------------------------------------------------
# def create_google_credentials(token):

#     if not token:
#         return None

#     return Credentials(
#         token=token.get("access_token"),
#         refresh_token=token.get("refresh_token"),
#         token_uri=TOKEN_ENDPOINT,
#         client_id=CLIENT_ID,
#         client_secret=CLIENT_SECRET,
#         scopes=SCOPES,
#     )


# # ---------------------------------------------------
# # BUILD GMAIL SERVICE FROM CREDENTIALS
# # ---------------------------------------------------
# def build_gmail_service(creds):

#     return build(
#         "gmail",
#         "v1",
#         credentials=creds,
#     )


# # ---------------------------------------------------
# # SAVE / LOAD TOKEN ON DISK
# # ---------------------------------------------------
# def save_token(email, creds):

#     token_path = get_token_path(email)

#     os.makedirs(
#         os.path.dirname(token_path),
#         exist_ok=True,
#     )

#     with open(token_path, "w") as token_file:

#         token_file.write(creds.to_json())

#     clean_duplicate_tokens_safe()


# def load_saved_token(email):

#     token_path = get_token_path(email)

#     if not os.path.exists(token_path):
#         return None

#     return Credentials.from_authorized_user_file(
#         token_path,
#         SCOPES,
#     )


# def refresh_saved_token(creds):

#     if creds and creds.expired and creds.refresh_token:

#         creds.refresh(Request())

#     return creds


# # ---------------------------------------------------
# # AUTHENTICATE GMAIL (step 2 of the flow)
# # ---------------------------------------------------
# def authenticate_gmail():
#     """
#     Called once the OAuth token exists in session state
#     (either freshly granted via login_button(), or loaded
#     from a saved token.json for the active/auto-login
#     account). Builds Credentials, builds the Gmail service,
#     fetches the profile, and populates session state.
#     """

#     try:

#         creds = None

#         # -------------------------------------------
#         # PREFER A FRESH TOKEN FROM login_button()
#         # -------------------------------------------
#         raw_token = st.session_state.get("oauth_token")

#         if raw_token:

#             creds = create_google_credentials(raw_token)

#         # -------------------------------------------
#         # OTHERWISE FALL BACK TO A SAVED TOKEN FILE
#         # -------------------------------------------
#         if not creds:

#             temp_email = st.session_state.get("email", "")

#             creds = load_saved_token(temp_email)

#         if not creds:

#             st.error("❌ No credentials available. Please log in.")

#             return None

#         # -------------------------------------------
#         # REFRESH IF NEEDED
#         # -------------------------------------------
#         if not creds.valid:

#             try:

#                 creds = refresh_saved_token(creds)

#             except Exception:

#                 st.error("❌ Session expired. Please log in again.")

#                 clear_session()

#                 return None

#         # -------------------------------------------
#         # BUILD GMAIL SERVICE
#         # -------------------------------------------
#         service = build_gmail_service(creds)

#         # -------------------------------------------
#         # FETCH PROFILE
#         # -------------------------------------------
#         profile = (
#             service.users()
#             .getProfile(userId="me")
#             .execute()
#         )

#         email = profile.get("emailAddress", "")

#         if not email:

#             st.error("❌ Could not retrieve Gmail address.")

#             return None

#         # -------------------------------------------
#         # SAVE TOKEN
#         # -------------------------------------------
#         save_token(email, creds)

#         # -------------------------------------------
#         # UPDATE ACCOUNTS
#         # -------------------------------------------
#         if email not in st.session_state.accounts:

#             st.session_state.accounts.append(email)

#         # -------------------------------------------
#         # SESSION STATE
#         # -------------------------------------------
#         st.session_state.email = email

#         st.session_state.user_id = (
#             email.split("@")[0].capitalize()
#         )

#         st.session_state.logged_in = True

#         st.session_state.service = service

#         st.session_state.fetch_on_login = True

#         st.session_state.fetching_in_progress = False

#         st.session_state.force_fetch = False

#         st.session_state.logout_triggered = False

#         st.session_state.switching_account = False

#         st.session_state.auto_login_checked = False

#         st.session_state.last_active = None

#         # keep the raw token around for refresh_token()/revoke_token()
#         st.session_state.oauth_token = json.loads(creds.to_json())

#         st.toast(f"✅ Connected: {email}")

#         return service

#     except Exception as e:

#         st.error(f"❌ Authentication Error: {e}")

#         return None


# # ---------------------------------------------------
# # GET GMAIL SERVICE
# # ---------------------------------------------------
# def get_gmail_service(email=""):

#     return authenticate_gmail()


# # ---------------------------------------------------
# # LOAD EXISTING ACCOUNT SERVICE
# # ---------------------------------------------------
# def load_account_service(email):

#     try:

#         creds = load_saved_token(email)

#         if not creds:

#             st.error("❌ Token not found.")

#             return None

#         creds = refresh_saved_token(creds)

#         service = build_gmail_service(creds)

#         return service

#     except Exception as e:

#         st.error(f"❌ Failed loading account: {e}")

#         return None


# # ---------------------------------------------------
# # AUTO LOGIN
# # ---------------------------------------------------
# def auto_login():

#     if (
#         not st.session_state.get("logged_in", False)
#         and not st.session_state.get("auto_login_checked", False)
#         and st.session_state.get("accounts", [])
#     ):

#         for saved_email in st.session_state.accounts:

#             try:

#                 creds = load_saved_token(saved_email)

#                 if not creds:
#                     continue

#                 # -------------------------------
#                 # REFRESH TOKEN
#                 # -------------------------------
#                 if creds.expired and creds.refresh_token:

#                     try:

#                         creds.refresh(Request())

#                     except Exception:

#                         continue

#                 # -------------------------------
#                 # VALID TOKEN
#                 # -------------------------------
#                 if creds.valid:

#                     save_token(saved_email, creds)

#                     service = build_gmail_service(creds)

#                     st.session_state.email = saved_email

#                     st.session_state.user_id = (
#                         saved_email.split("@")[0].capitalize()
#                     )

#                     st.session_state.service = service

#                     st.session_state.oauth_token = json.loads(
#                         creds.to_json()
#                     )

#                     st.session_state.logged_in = True

#                     st.session_state.fetch_on_login = True

#                     st.toast(f"✅ Auto-logged in as {saved_email}")

#                     break

#             except Exception:

#                 continue

#         st.session_state.auto_login_checked = True


# # ---------------------------------------------------
# # LOGOUT
# # ---------------------------------------------------
# def logout(remember_me=True):
#     """
#     Revokes the current OAuth token via streamlit-oauth's
#     revoke endpoint, then clears session state. If
#     remember_me is False, also deletes the saved token.json
#     so the user is required to log in again next visit.
#     """

#     token = st.session_state.get("oauth_token")

#     if token:

#         try:

#             _oauth2.revoke_token(
#                 token=token,
#                 token_type="access_token",
#             )

#         except Exception:
#             # Revocation failing shouldn't block logout locally
#             pass

#     if not remember_me:

#         email = st.session_state.get("email", "")

#         token_path = get_token_path(email)

#         if os.path.exists(token_path):

#             os.remove(token_path)

#         if email in st.session_state.get("accounts", []):

#             st.session_state.accounts.remove(email)

#     if "oauth_token" in st.session_state:

#         del st.session_state["oauth_token"]

#     clear_session()


# # ---------------------------------------------------
# # CLEAR SESSION
# # ---------------------------------------------------
# def clear_session(keys=None):

#     if keys is None:

#         keys = [
#             "logged_in",
#             "email",
#             "user_id",
#             "service",
#             "spam_emails",
#             "ham_emails",
#             "sender_count",
#             "recipient_count",
#             "fetch_on_login",
#             "fetching_in_progress",
#             "force_fetch",
#             "show_login_prompt",
#         ]

#     # -----------------------------------------------
#     # REMOVE KEYS
#     # -----------------------------------------------
#     for key in keys:

#         if key in st.session_state:

#             del st.session_state[key]

#     # -----------------------------------------------
#     # SAFE RESETS
#     # -----------------------------------------------
#     st.session_state.logged_in = False

#     st.session_state.service = None

#     st.session_state.fetch_on_login = False

#     st.session_state.fetching_in_progress = False

#     st.session_state.force_fetch = False

#     st.session_state.logout_triggered = True

#     st.session_state.switching_account = False

#     st.session_state.auto_login_checked = False

#     st.session_state.spam_emails = []

#     st.session_state.ham_emails = []

#     st.session_state.sender_count = {}

#     st.session_state.recipient_count = {}

#     st.session_state.last_fetch_time = None