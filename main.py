# mailshield/main_app.py

import streamlit as st
# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(

    page_title="🛡️ MailShield",

    page_icon="📧",

    layout="wide"
)
import streamlit.components.v1 as components
from datetime import datetime

# ---------------------------------------------------
# DATABASE
# ---------------------------------------------------
from database.db import initialize_database

# ---------------------------------------------------
# AUTH
# ---------------------------------------------------
from auth import (
    auto_login,
    authenticate_gmail,
    clear_session
)
from oauth_google import handle_callback

# ---------------------------------------------------
# CLASSIFIER
# ---------------------------------------------------
from classifier import (
    classify_message,
    load_model_and_vectorizer
)

# ---------------------------------------------------
# FETCHER
# ---------------------------------------------------
from fetcher import (
    fetch_and_classify_emails
)

# ---------------------------------------------------
# SESSION
# ---------------------------------------------------
from utils.session import (
    handle_session_timeout,
    update_last_active,
    initialize_session_state
)

# ---------------------------------------------------
# UI
# ---------------------------------------------------
from ui.sidebar import (
    render_sidebar
)

from ui.dashboard import (
    display_metrics,
    display_email_tabs,
    display_chart
)

from ui.export import (
    export_buttons
)

from ui.multi_insights import (
    render_multi_account_insights
)

from ui.analytics import (
    render_analytics_dashboard
)

from utils.logger import (
    log_info,
    log_error
)
from database.queries import (
    load_emails_from_db,
    get_email_count_for_days
)
# ---------------------------------------------------
# INITIALIZE SESSION
# ---------------------------------------------------
initialize_session_state()
handle_callback()
# -----------------------------------------------
# LOAD OLD EMAILS ON START (IMPORTANT)
# -----------------------------------------------
if "spam_emails" not in st.session_state:
    st.session_state.spam_emails = []

if "ham_emails" not in st.session_state:
    st.session_state.ham_emails = []

# ---------------------------------------------------
# INITIALIZE DATABASE
# ---------------------------------------------------
initialize_database()

# ---------------------------------------------------
# HANDLE SESSION TIMEOUT
# ---------------------------------------------------
handle_session_timeout()

if (

    not st.session_state.get("logged_in", False)

    and

    not st.session_state.get("oauth_callback", False)

    and

    not st.session_state.get("auto_login_checked", False)

    and

    st.session_state.get("accounts")

    and

    not st.session_state.get("logout_triggered", False)

    and

    not st.session_state.get("switching_account", False)

    and

    not st.session_state.get("session_timed_out", False)

):
    auto_login()

    st.session_state.auto_login_checked = True

if (
    not st.session_state.get("logged_in", False)
    and st.session_state.get("oauth_token")
    and not st.session_state.get("logout_triggered", False)
    and not st.session_state.get("switching_account", False)
):
    authenticate_gmail()

# ---------------------------------------------------
# UPDATE LAST ACTIVE
# ---------------------------------------------------
update_last_active()

# ---------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------
model, vectorizer = load_model_and_vectorizer()

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
show_multi_insights = render_sidebar()

# -----------------------------------------------
# LOAD / RELOAD EMAILS AFTER SIDEBAR (CORRECT)
# -----------------------------------------------

# init lists
if "spam_emails" not in st.session_state:
    st.session_state.spam_emails = []

if "ham_emails" not in st.session_state:
    st.session_state.ham_emails = []

# init tracker
if "last_email_limit" not in st.session_state:
    st.session_state.last_email_limit = None

if "last_scan_days" not in st.session_state:
    st.session_state.last_scan_days = None

settings_changed = (

    st.session_state.email_limit
    != st.session_state.last_email_limit

    or

    st.session_state.scan_days
    != st.session_state.last_scan_days
)

first_load = (
    not st.session_state.spam_emails
    and
    not st.session_state.ham_emails
)

if (first_load or settings_changed) and st.session_state.get("email"):

    # -----------------------------------------------
    # RESET "LOADED" MESSAGE IF SETTINGS CHANGED
    # -----------------------------------------------
    if settings_changed:
        st.session_state.load_message_shown = False

    requested_limit = st.session_state.email_limit

    available_count = get_email_count_for_days(
        st.session_state.email,
        st.session_state.scan_days
    )

    # -----------------------------------------------
    # NEED MORE HISTORICAL EMAILS -> TRIGGER A FETCH
    # -----------------------------------------------
    # (The dashboard will still show whatever is already
    # stored below; the fetch step further down refreshes
    # it once new data arrives, so we don't need to load
    # from the DB twice here.)
    # -----------------------------------------------
    if available_count < requested_limit:

        st.session_state.force_fetch = True

    # -----------------------------------------------
    # LOAD ONCE FROM DB (COVERS BOTH CASES ABOVE)
    # -----------------------------------------------
    spam, ham = load_emails_from_db(
        st.session_state.email,
        limit=requested_limit,
        days=st.session_state.scan_days
    )

    st.session_state.spam_emails = spam
    st.session_state.ham_emails = ham

    st.session_state.last_email_limit = st.session_state.email_limit
    st.session_state.last_scan_days = st.session_state.scan_days

    if not st.session_state.get("load_message_shown", False):
        st.success(f"Loaded {len(spam) + len(ham)} emails")
        st.session_state.load_message_shown = True

# ---------------------------------------------------
# MAIN APP
# ---------------------------------------------------
if st.session_state.get("logged_in"):

    st.header("📥 Inbox Classification")

    st.divider()

    # -----------------------------------------------
    # FETCH FLAGS
    # -----------------------------------------------
    fetching = (

        st.session_state.get(
            "force_fetch",
            False
        )

        or

        st.session_state.get(
            "fetch_on_login",
            False
        )
    )

    # -----------------------------------------------
    # FETCH EMAILS
    # -----------------------------------------------
    if fetching:

        st.session_state.fetching_in_progress = True

        with st.spinner(
            "🔍 Fetching and analyzing emails..."
        ):

            try:

                result = fetch_and_classify_emails(

                service = st.session_state.service,

                model=model,

                vectorizer=vectorizer
         )

                # -----------------------------------
                # HANDLE INCREMENTAL RESULT (FIX)
                # -----------------------------------
                if result is not None:

                    spam, ham, sender_count, recipient_count, error_log = result

                    spam_db, ham_db = load_emails_from_db(
                        st.session_state.email,
                        limit=st.session_state.email_limit,
                        days=st.session_state.scan_days
                        )

                    st.session_state.spam_emails = spam_db
                    st.session_state.ham_emails = ham_db
                    st.session_state.sender_count = sender_count
                    st.session_state.recipient_count = recipient_count
                    st.session_state.load_message_shown = False
                    st.session_state.fetch_count += 1
                    st.session_state.last_fetch_time = datetime.now()
                    st.session_state.last_active = datetime.now()

                    # -----------------------------------
                    # ERROR LOG (RESTORE THIS)
                    # -----------------------------------
                    if error_log:

                        with st.expander("⚠️ Show Errors"):

                            for err in error_log:
                                st.error(
                                   f"{err.get('message_id')} — {err.get('error')}"
                   )

            except Exception as e:

                st.error(
                    f"❌ Failed to fetch emails: {e}"
                )

            finally:

                st.session_state.force_fetch = False

                st.session_state.fetch_on_login = False

                st.session_state.fetching_in_progress = False

    # -----------------------------------------------
    # MANUAL FETCH BUTTON
    # -----------------------------------------------
    if not fetching:

        st.subheader("📥 Inbox Analysis")

        if st.button(
            "🔍 Analyze My Inbox",
            use_container_width=True
        ):

            st.session_state.force_fetch = True

            st.rerun()

    # -----------------------------------------------
    # HIDE DASHBOARD DURING FETCH
    # -----------------------------------------------
    if st.session_state.get("fetching_in_progress"):

         st.stop()

    # -----------------------------------------------
    # FILTERS
    # -----------------------------------------------
    st.divider()

    st.subheader("🔍 Filter Emails")

    search = st.text_input(
        "Search by Subject, Sender, or Recipient"
    ).lower()

    # -----------------------------------------------
    # FILTER SPAM
    # -----------------------------------------------
    spam_emails = [

        e

        for e in st.session_state.spam_emails

        if (

            search in e["subject"].lower()

            or

            search in e["sender"].lower()

            or

            search in e["recipient"].lower()

        )

    ] if search else st.session_state.spam_emails

    # -----------------------------------------------
    # FILTER HAM
    # -----------------------------------------------
    ham_emails = [

        e

        for e in st.session_state.ham_emails

        if (

            search in e["subject"].lower()

            or

            search in e["sender"].lower()

            or

            search in e["recipient"].lower()

        )

    ] if search else st.session_state.ham_emails

    # -----------------------------------------------
    # DASHBOARD
    # -----------------------------------------------
    st.divider()

    st.subheader("📈 Classification Summary")

    display_metrics(
        spam_emails,
        ham_emails
    )

    # -----------------------------------------------
    # CHART
    # -----------------------------------------------
    if (
        spam_emails
        or ham_emails
    ) and st.checkbox(
        "📊 Show Classification Chart"
    ):

        display_chart(
            spam_emails,
            ham_emails
        )

    # -----------------------------------------------
    # EXPORTS
    # -----------------------------------------------
    export_buttons(
        spam_emails,
        ham_emails
    )

    # -----------------------------------------------
    # EMAIL TABS
    # -----------------------------------------------
    display_email_tabs(
        spam_emails,
        ham_emails
    )

    # -----------------------------------------------
    # HISTORICAL ANALYTICS
    # -----------------------------------------------
    render_analytics_dashboard()

else:

    st.warning(
        "🔐 Please log in with a Gmail account. "
        "Use \"Connect First Gmail Account\" in the sidebar to sign in."
    )

# ---------------------------------------------------
# MULTI ACCOUNT INSIGHTS
# ---------------------------------------------------
if show_multi_insights:

    render_multi_account_insights(

        accounts=st.session_state.accounts,

        multi_stats_cache=st.session_state.get(
            "multi_account_stats",
            {}
        ),

        refresh=st.session_state.get(
            "refresh_multi_stats",
            False
        )
    )

# ---------------------------------------------------
# LIVE CLASSIFIER
# ---------------------------------------------------
if not st.session_state.get("logged_in"):

    st.markdown("---")

    st.header("📝 Live Text Spam Classifier")

    input_text = st.text_area(
        "Paste email content here:",
        height=200
    )

    if (
        input_text
        and st.button("🚀 Classify Text")
    ):

        with st.spinner(
            "⏳ Classifying..."
        ):

            result, confidence = classify_message(

                input_text,

                model,

                vectorizer
            )

            st.success(

                f"Prediction: {result} "

                f"with {confidence}% confidence"

            )

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------
st.markdown("---")

st.markdown(
    """
    <center>
    <sub>
    © 2026 Vishwakarma Government Engineering College
    • Project by Nandan | Krishna | Jay | Ayush
    • All Rights Reserved
    </sub>
    </center>
    """,
    unsafe_allow_html=True
)
# import streamlit as st

# # ---------------------------------------------------
# # PAGE CONFIG
# # ---------------------------------------------------
# st.set_page_config(

#     page_title="🛡️ MailShield",

#     page_icon="📧",

#     layout="wide"
# )

# from datetime import datetime

# # ---------------------------------------------------
# # DATABASE
# # ---------------------------------------------------
# from database.db import initialize_database

# # ---------------------------------------------------
# # AUTH
# # ---------------------------------------------------
# from auth import (
#     auto_login,
#     clear_session
# )

# # ---------------------------------------------------
# # CLASSIFIER
# # ---------------------------------------------------
# from classifier import (
#     classify_message,
#     load_model_and_vectorizer
# )

# # ---------------------------------------------------
# # FETCHER
# # ---------------------------------------------------
# from fetcher import (
#     fetch_and_classify_emails
# )

# # ---------------------------------------------------
# # SESSION
# # ---------------------------------------------------
# from utils.session import (
#     handle_session_timeout,
#     update_last_active,
#     initialize_session_state
# )

# # ---------------------------------------------------
# # UI
# # ---------------------------------------------------
# from ui.sidebar import (
#     render_sidebar
# )

# from ui.dashboard import (
#     display_metrics,
#     display_email_tabs,
#     display_chart
# )

# from ui.export import (
#     export_buttons
# )

# from ui.multi_insights import (
#     render_multi_account_insights
# )

# from ui.analytics import (
#     render_analytics_dashboard
# )

# from utils.logger import (
#     log_info,
#     log_error
# )
# from database.queries import (
#     load_emails_from_db,
#     get_email_count_for_days
# )
# # ---------------------------------------------------
# # INITIALIZE SESSION
# # ---------------------------------------------------
# initialize_session_state()

# # -----------------------------------------------
# # LOAD OLD EMAILS ON START (IMPORTANT)
# # -----------------------------------------------
# if "spam_emails" not in st.session_state:
#     st.session_state.spam_emails = []

# if "ham_emails" not in st.session_state:
#     st.session_state.ham_emails = []

# # ---------------------------------------------------
# # INITIALIZE DATABASE
# # ---------------------------------------------------
# initialize_database()

# # ---------------------------------------------------
# # HANDLE SESSION TIMEOUT
# # ---------------------------------------------------
# handle_session_timeout()

# # ---------------------------------------------------
# # AUTO LOGIN
# # ---------------------------------------------------
# if (

#     not st.session_state.get(
#         "logged_in",
#         False
#     )

#     and

#     not st.session_state.get(
#         "auto_login_checked",
#         False
#     )

#     and

#     st.session_state.get(
#         "accounts"
#     )

#     and

#     not st.session_state.get(
#         "logout_triggered",
#         False
#     )

#     and

#     not st.session_state.get(
#         "switching_account",
#         False
#     )

#     and

#     not st.session_state.get(
#         "session_timed_out",
#         False
#     )
# ):

#     auto_login()

#     st.session_state.auto_login_checked = True
# # ---------------------------------------------------
# # UPDATE LAST ACTIVE
# # ---------------------------------------------------
# update_last_active()

# # ---------------------------------------------------
# # LOAD MODEL
# # ---------------------------------------------------
# model, vectorizer = load_model_and_vectorizer()

# # ---------------------------------------------------
# # SIDEBAR
# # ---------------------------------------------------
# show_multi_insights = render_sidebar()

# # -----------------------------------------------
# # LOAD / RELOAD EMAILS AFTER SIDEBAR (CORRECT)
# # -----------------------------------------------

# # init lists
# if "spam_emails" not in st.session_state:
#     st.session_state.spam_emails = []

# if "ham_emails" not in st.session_state:
#     st.session_state.ham_emails = []

# # init tracker
# if "last_email_limit" not in st.session_state:
#     st.session_state.last_email_limit = None

# if "last_scan_days" not in st.session_state:
#     st.session_state.last_scan_days = None

# settings_changed = (

#     st.session_state.email_limit
#     != st.session_state.last_email_limit

#     or

#     st.session_state.scan_days
#     != st.session_state.last_scan_days
# )

# first_load = (
#     not st.session_state.spam_emails
#     and
#     not st.session_state.ham_emails
# )

# if (first_load or settings_changed) and st.session_state.get("email"):

#     # -----------------------------------------------
#     # RESET "LOADED" MESSAGE IF SETTINGS CHANGED
#     # -----------------------------------------------
#     if settings_changed:
#         st.session_state.load_message_shown = False

#     requested_limit = st.session_state.email_limit

#     available_count = get_email_count_for_days(
#         st.session_state.email,
#         st.session_state.scan_days
#     )

#     # -----------------------------------------------
#     # NEED MORE HISTORICAL EMAILS -> TRIGGER A FETCH
#     # -----------------------------------------------
#     # (The dashboard will still show whatever is already
#     # stored below; the fetch step further down refreshes
#     # it once new data arrives, so we don't need to load
#     # from the DB twice here.)
#     # -----------------------------------------------
#     if available_count < requested_limit:

#         st.session_state.force_fetch = True

#     # -----------------------------------------------
#     # LOAD ONCE FROM DB (COVERS BOTH CASES ABOVE)
#     # -----------------------------------------------
#     spam, ham = load_emails_from_db(
#         st.session_state.email,
#         limit=requested_limit,
#         days=st.session_state.scan_days
#     )

#     st.session_state.spam_emails = spam
#     st.session_state.ham_emails = ham

#     st.session_state.last_email_limit = st.session_state.email_limit
#     st.session_state.last_scan_days = st.session_state.scan_days

#     if not st.session_state.get("load_message_shown", False):
#         st.success(f"Loaded {len(spam) + len(ham)} emails")
#         st.session_state.load_message_shown = True

# # ---------------------------------------------------
# # MAIN APP
# # ---------------------------------------------------
# if st.session_state.get("logged_in"):

#     st.header("📥 Inbox Classification")

#     st.divider()

#     # -----------------------------------------------
#     # FETCH FLAGS
#     # -----------------------------------------------
#     fetching = (

#         st.session_state.get(
#             "force_fetch",
#             False
#         )

#         or

#         st.session_state.get(
#             "fetch_on_login",
#             False
#         )
#     )

#     # -----------------------------------------------
#     # FETCH EMAILS
#     # -----------------------------------------------
#     if fetching:

#         st.session_state.fetching_in_progress = True

#         with st.spinner(
#             "🔍 Fetching and analyzing emails..."
#         ):

#             try:

#                 result = fetch_and_classify_emails(

#                 service = st.session_state.service,

#                 model=model,

#                 vectorizer=vectorizer
#          )

#                 # -----------------------------------
#                 # HANDLE INCREMENTAL RESULT (FIX)
#                 # -----------------------------------
#                 if result is not None:

#                     spam, ham, sender_count, recipient_count, error_log = result

#                     spam_db, ham_db = load_emails_from_db(
#                         st.session_state.email,
#                         limit=st.session_state.email_limit,
#                         days=st.session_state.scan_days
#                         )

#                     st.session_state.spam_emails = spam_db
#                     st.session_state.ham_emails = ham_db
#                     st.session_state.sender_count = sender_count
#                     st.session_state.recipient_count = recipient_count
#                     st.session_state.load_message_shown = False
#                     st.session_state.fetch_count += 1
#                     st.session_state.last_fetch_time = datetime.now()
#                     st.session_state.last_active = datetime.now()

#                     # -----------------------------------
#                     # ERROR LOG (RESTORE THIS)
#                     # -----------------------------------
#                     if error_log:

#                         with st.expander("⚠️ Show Errors"):

#                             for err in error_log:
#                                 st.error(
#                                    f"{err.get('message_id')} — {err.get('error')}"
#                    )

#             except Exception as e:

#                 st.error(
#                     f"❌ Failed to fetch emails: {e}"
#                 )

#             finally:

#                 st.session_state.force_fetch = False

#                 st.session_state.fetch_on_login = False

#                 st.session_state.fetching_in_progress = False

#     # -----------------------------------------------
#     # MANUAL FETCH BUTTON
#     # -----------------------------------------------
#     if not fetching:

#         st.subheader("📥 Inbox Analysis")

#         if st.button(
#             "🔍 Analyze My Inbox",
#             use_container_width=True
#         ):

#             st.session_state.force_fetch = True

#             st.rerun()

#     # -----------------------------------------------
#     # HIDE DASHBOARD DURING FETCH
#     # -----------------------------------------------
#     if st.session_state.get("fetching_in_progress"):

#          st.stop()

#     # -----------------------------------------------
#     # FILTERS
#     # -----------------------------------------------
#     st.divider()

#     st.subheader("🔍 Filter Emails")

#     search = st.text_input(
#         "Search by Subject, Sender, or Recipient"
#     ).lower()

#     # -----------------------------------------------
#     # FILTER SPAM
#     # -----------------------------------------------
#     spam_emails = [

#         e

#         for e in st.session_state.spam_emails

#         if (

#             search in e["subject"].lower()

#             or

#             search in e["sender"].lower()

#             or

#             search in e["recipient"].lower()

#         )

#     ] if search else st.session_state.spam_emails

#     # -----------------------------------------------
#     # FILTER HAM
#     # -----------------------------------------------
#     ham_emails = [

#         e

#         for e in st.session_state.ham_emails

#         if (

#             search in e["subject"].lower()

#             or

#             search in e["sender"].lower()

#             or

#             search in e["recipient"].lower()

#         )

#     ] if search else st.session_state.ham_emails

#     # -----------------------------------------------
#     # DASHBOARD
#     # -----------------------------------------------
#     st.divider()

#     st.subheader("📈 Classification Summary")

#     display_metrics(
#         spam_emails,
#         ham_emails
#     )

#     # -----------------------------------------------
#     # CHART
#     # -----------------------------------------------
#     if (
#         spam_emails
#         or ham_emails
#     ) and st.checkbox(
#         "📊 Show Classification Chart"
#     ):

#         display_chart(
#             spam_emails,
#             ham_emails
#         )

#     # -----------------------------------------------
#     # EXPORTS
#     # -----------------------------------------------
#     export_buttons(
#         spam_emails,
#         ham_emails
#     )

#     # -----------------------------------------------
#     # EMAIL TABS
#     # -----------------------------------------------
#     display_email_tabs(
#         spam_emails,
#         ham_emails
#     )

#     # -----------------------------------------------
#     # HISTORICAL ANALYTICS
#     # -----------------------------------------------
#     render_analytics_dashboard()

# else:

#     st.warning(
#         "🔐 Please log in with a Gmail account."
#     )

# # ---------------------------------------------------
# # MULTI ACCOUNT INSIGHTS
# # ---------------------------------------------------
# if show_multi_insights:

#     render_multi_account_insights(

#         accounts=st.session_state.accounts,

#         multi_stats_cache=st.session_state.get(
#             "multi_account_stats",
#             {}
#         ),

#         refresh=st.session_state.get(
#             "refresh_multi_stats",
#             False
#         )
#     )

# # ---------------------------------------------------
# # LIVE CLASSIFIER
# # ---------------------------------------------------
# if not st.session_state.get("logged_in"):

#     st.markdown("---")

#     st.header("📝 Live Text Spam Classifier")

#     input_text = st.text_area(
#         "Paste email content here:",
#         height=200
#     )

#     if (
#         input_text
#         and st.button("🚀 Classify Text")
#     ):

#         with st.spinner(
#             "⏳ Classifying..."
#         ):

#             result, confidence = classify_message(

#                 input_text,

#                 model,

#                 vectorizer
#             )

#             st.success(

#                 f"Prediction: {result} "

#                 f"with {confidence}% confidence"

#             )

# # ---------------------------------------------------
# # FOOTER
# # ---------------------------------------------------
# st.markdown("---")

# st.markdown(
#     """
#     <center>
#     <sub>
#     © 2026 Vishwakarma Government Engineering College
#     • Project by Nandan | Krishna | Jay | Ayush
#     • All Rights Reserved
#     </sub>
#     </center>
#     """,
#     unsafe_allow_html=True
# )
