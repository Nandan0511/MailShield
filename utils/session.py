# # 🕒 utils/session.py
# 🕒 utils/session.py

import os
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
    decode_path_to_email
)

from utils.cookies import get_device_id


# ---------------------------------------------------
# GET ACCOUNTS SAVED FOR THIS DEVICE ONLY
# ---------------------------------------------------
def get_accounts_for_device(device_id):

    if not device_id:
        return []

    device_folder = os.path.join("tokens", device_id)

    if not os.path.exists(device_folder):
        return []

    accounts = []

    for folder in os.listdir(device_folder):

        token_path = os.path.join(
            device_folder, folder, "token.json"
        )

        if os.path.exists(token_path):
            accounts.append(decode_path_to_email(folder))

    return sorted(accounts)


# ---------------------------------------------------
# INITIALIZE SESSION STATE
# ---------------------------------------------------
def initialize_session_state():

    # -----------------------------------------------
    # RESOLVE DEVICE ID FIRST — "accounts" below
    # depends on it being available already
    # -----------------------------------------------
    if "device_id" not in st.session_state:
        st.session_state["device_id"] = get_device_id()

    device_id = st.session_state.get("device_id")

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

                # only this device's saved accounts —
                # never another device's tokens
                st.session_state[key] = get_accounts_for_device(device_id)

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

def get_most_recent_account(device_id):
    """
    Returns the email of the most recently added/modified
    token for this device, based on file modification time.
    Used to auto-login right after adding a new account.
    """
    if not device_id:
        return None

    device_folder = os.path.join("tokens", device_id)

    if not os.path.exists(device_folder):
        return None

    newest_email = None
    newest_mtime = -1

    for folder in os.listdir(device_folder):
        token_path = os.path.join(device_folder, folder, "token.json")
        if os.path.exists(token_path):
            mtime = os.path.getmtime(token_path)
            if mtime > newest_mtime:
                newest_mtime = mtime
                newest_email = decode_path_to_email(folder)

    return newest_email