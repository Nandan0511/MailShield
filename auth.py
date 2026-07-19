# 🔐 auth.py
# FINAL STABLE VERSION

import os
import streamlit as st

from google.oauth2.credentials import Credentials

from google_auth_oauthlib.flow import (
    InstalledAppFlow
)

from googleapiclient.discovery import build

from google.auth.transport.requests import (
    Request
)

from config import SCOPES

from utils.token_utils import (
    get_token_path,
    clean_duplicate_tokens_safe,
)

from utils.session import (
    initialize_session_state
)

initialize_session_state()


# ---------------------------------------------------
# AUTHENTICATE GMAIL
# ---------------------------------------------------
def authenticate_gmail():

    try:

        creds = None

        temp_email = st.session_state.get(
            "email",
            ""
        )

        temp_token_path = get_token_path(
            temp_email
        )

        # -------------------------------------------
        # LOAD EXISTING TOKEN
        # -------------------------------------------
        if os.path.exists(temp_token_path):

            creds = (
                Credentials.from_authorized_user_file(
                    temp_token_path,
                    SCOPES
                )
            )

        # -------------------------------------------
        # REFRESH OR LOGIN
        # -------------------------------------------
        if not creds or not creds.valid:

            try:

                if (
                    creds
                    and creds.expired
                    and creds.refresh_token
                ):

                    creds.refresh(Request())

                else:

                    raise Exception(
                        "Invalid token"
                    )

            except:

                client_config = {
                    "installed": {
                        "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                        "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [
                            "http://localhost"
                        ]
                    }
                }

                flow = InstalledAppFlow.from_client_config(
                    client_config,
                    SCOPES
                )

                # flow = (
                #     InstalledAppFlow
                #     .from_client_secrets_file(

                #         "credentials.json",

                #         SCOPES
                #     )
                # )

                with st.spinner(
                    "🔐 Opening Google Login..."
                ):

                    creds = flow.run_local_server(

                        port=0,

                        open_browser=True,

                        prompt="consent"
                    )

        # -------------------------------------------
        # BUILD GMAIL SERVICE
        # -------------------------------------------
        service = build(

            "gmail",

            "v1",

            credentials=creds
        )

        # -------------------------------------------
        # FETCH PROFILE
        # -------------------------------------------
        profile = (

            service.users()
            .getProfile(
                userId="me"
            )
            .execute()
        )

        email = profile.get(
            "emailAddress",
            ""
        )

        if not email:

            st.error(
                "❌ Could not retrieve Gmail address."
            )

            return None

        # -------------------------------------------
        # SAVE TOKEN
        # -------------------------------------------
        token_path = get_token_path(
            email
        )

        os.makedirs(

            os.path.dirname(token_path),

            exist_ok=True
        )

        with open(
            token_path,
            "w"
        ) as token_file:

            token_file.write(
                creds.to_json()
            )

        clean_duplicate_tokens_safe()

        # -------------------------------------------
        # UPDATE ACCOUNTS
        # -------------------------------------------
        if (
            email
            not in st.session_state.accounts
        ):

            st.session_state.accounts.append(
                email
            )

        # -------------------------------------------
        # SESSION STATE
        # -------------------------------------------
        st.session_state.email = email

        st.session_state.user_id = (
            email.split("@")[0]
            .capitalize()
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

        st.toast(
            f"✅ Connected: {email}"
        )

        return service

    except Exception as e:

        st.error(
            f"❌ Authentication Error: {e}"
        )

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

        token_path = get_token_path(
            email
        )

        if not os.path.exists(token_path):

            st.error(
                "❌ Token not found."
            )

            return None

        creds = Credentials.from_authorized_user_file(

            token_path,

            SCOPES
        )

        # -------------------------------------------
        # REFRESH TOKEN
        # -------------------------------------------
        if (
            creds.expired
            and creds.refresh_token
        ):

            creds.refresh(Request())

        # -------------------------------------------
        # BUILD SERVICE
        # -------------------------------------------
        service = build(

            "gmail",

            "v1",

            credentials=creds
        )

        return service

    except Exception as e:

        st.error(
            f"❌ Failed loading account: {e}"
        )

        return None
# ---------------------------------------------------
# AUTO LOGIN
# ---------------------------------------------------
def auto_login():

    if (

        not st.session_state.get(
            "logged_in",
            False
        )

        and

        not st.session_state.get(
            "auto_login_checked",
            False
        )

        and

        st.session_state.get(
            "accounts",
            []
        )
    ):

        for saved_email in (
            st.session_state.accounts
        ):

            token_path = get_token_path(
                saved_email
            )

            if os.path.exists(token_path):

                try:

                    creds = (
                        Credentials
                        .from_authorized_user_file(

                            token_path,

                            SCOPES
                        )
                    )

                    # -------------------------------
                    # REFRESH TOKEN
                    # -------------------------------
                    if (
                        creds.expired
                        and creds.refresh_token
                    ):

                        try:

                            creds.refresh(
                                Request()
                            )

                        except Exception:

                            continue

                    # -------------------------------
                    # VALID TOKEN
                    # -------------------------------
                    if creds.valid:

                        service = build(

                            "gmail",

                            "v1",

                            credentials=creds
                        )

                        st.session_state.email = (
                            saved_email
                        )

                        st.session_state.user_id = (

                            saved_email
                            .split("@")[0]
                            .capitalize()
                        )

                        st.session_state.service = (
                            service
                        )

                        st.session_state.logged_in = True

                        st.session_state.fetch_on_login = True

                        st.toast(

                            f"✅ Auto-logged in as {saved_email}"
                        )

                        break

                except Exception:

                    continue

        st.session_state.auto_login_checked = True


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

            "show_login_prompt"
        ]

    # -----------------------------------------------
    # REMOVE KEYS
    # -----------------------------------------------
    for key in keys:

        if key in st.session_state:

            del st.session_state[key]

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
