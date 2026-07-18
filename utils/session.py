# 🕒 utils/session.py

from datetime import (
    datetime,
    timedelta
)

import streamlit as st

from collections import defaultdict

from config import (
    SESSION_DEFAULTS,
    SESSION_TIMEOUT_MINUTES
)

from utils.token_utils import (
    load_existing_accounts
)


# ---------------------------------------------------
# INITIALIZE SESSION STATE
# ---------------------------------------------------
def initialize_session_state():

    for key, value in SESSION_DEFAULTS.items():

        if key not in st.session_state:

            # ---------------------------------------
            # MUTABLE OBJECTS
            # ---------------------------------------
            if key == "spam_emails":

                st.session_state[key] = []

            elif key == "ham_emails":

                st.session_state[key] = []

            elif key == "sender_count":

                st.session_state[key] = defaultdict(int)

            elif key == "recipient_count":

                st.session_state[key] = defaultdict(int)

            elif key == "accounts":

                st.session_state[key] = (
                    load_existing_accounts()
                )

            elif key == "multi_account_stats":

                st.session_state[key] = {}

            else:

                st.session_state[key] = value


# ---------------------------------------------------
# HANDLE SESSION TIMEOUT
# ---------------------------------------------------
def handle_session_timeout():

    if (
        st.session_state.get("logged_in")
        and "last_active" in st.session_state
    ):

        last_active = st.session_state[
            "last_active"
        ]

        now = datetime.now()

        if (

            now - last_active

            > timedelta(
                minutes=SESSION_TIMEOUT_MINUTES
            )
        ):

            if not st.session_state.get(
                "timeout_handled",
                False
            ):

                st.session_state[
                    "session_timed_out"
                ] = True

                st.session_state[
                    "show_login_prompt"
                ] = True

                st.session_state[
                    "timeout_handled"
                ] = True

                # -----------------------------------
                # CLEAR SESSION KEYS
                # -----------------------------------
                for key in [

                    "logged_in",

                    "email",

                    "service",

                    "auto_login_checked"

                ]:

                    st.session_state.pop(
                        key,
                        None
                    )

                st.warning(
                    "🔒 Session expired."
                )

                st.info(
                    "👉 Please log in again."
                )

                st.rerun()

                return True

    return False


# ---------------------------------------------------
# UPDATE LAST ACTIVE
# ---------------------------------------------------
def update_last_active():

    if st.session_state.get("logged_in"):

        st.session_state[
            "last_active"
        ] = datetime.now()
