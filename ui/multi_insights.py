# 📈 ui/multi_insights.py

import os
import time
import pandas as pd
import streamlit as st
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from config import SCOPES
from classifier import (
    classify_message,
    load_model_and_vectorizer
)

# from utils.session import (
#     initialize_session_state
# )

from utils.token_utils import (
    get_token_path
)

from utils.email_utils import (
    batch_get_email_contents
)

# initialize_session_state()


# ---------------------------------------------------
# LOAD MODEL (CACHED)
# ---------------------------------------------------
model, vectorizer = load_model_and_vectorizer()


# ---------------------------------------------------
# FETCH ACCOUNT STATS
# ---------------------------------------------------
@st.cache_data(ttl=300)
def fetch_account_stats(
    email,
    scan_days=7,
    email_limit=50
):

    token_path = get_token_path(st.session_state.get("device_id"), email)

    if not os.path.exists(token_path):

        return None

    try:

        creds = Credentials.from_authorized_user_file(
            token_path,
            SCOPES
        )

        if not creds.valid:

            return None

        service = build(
            "gmail",
            "v1",
            credentials=creds
        )

        # -------------------------------------------
        # FETCH MESSAGE IDS
        # -------------------------------------------
        result = service.users().messages().list(
            userId="me",
            q=f"newer_than:{scan_days}d",
            maxResults=email_limit
        ).execute()

        messages = result.get(
            "messages",
            []
        )

        if not messages:

            return {
                "Email": email,
                "HAM": 0,
                "SPAM": 0,
                "Total": 0
            }

        # -------------------------------------------
        # BATCH FETCH EMAILS
        # -------------------------------------------
        message_ids = [

            msg["id"]

            for msg in messages
        ]

        emails = batch_get_email_contents(
            service,
            message_ids
        )

        spam_count = 0

        ham_count = 0

        # -------------------------------------------
        # PARALLEL CLASSIFICATION
        # -------------------------------------------
        def classify_email(email_data):

            if "error" in email_data:

                return None

            pred, _ = classify_message(
                email_data["content"],
                model,
                vectorizer
            )

            return pred

        with ThreadPoolExecutor(
            max_workers=10
        ) as executor:

            predictions = list(

                executor.map(
                    classify_email,
                    emails
                )
            )

        for pred in predictions:

            if pred == "🚫 SPAM":

                spam_count += 1

            elif pred == "✅ HAM":

                ham_count += 1

        return {

            "Email": email,

            "HAM": ham_count,

            "SPAM": spam_count,

            "Total": ham_count + spam_count,

            "Last Scan": time.strftime(
                "%Y-%m-%d %I:%M %p"
            )
        }

    except Exception as e:

        return {
            "Email": email,
            "HAM": 0,
            "SPAM": 0,
            "Total": 0,
            "Error": str(e)
        }



# ---------------------------------------------------
# RENDER MULTI ACCOUNT INSIGHTS
# ---------------------------------------------------
def render_multi_account_insights(
    accounts,
    multi_stats_cache,
    refresh=False
):

    # -----------------------------------------------
    # VALIDATION
    # -----------------------------------------------
    if not (
        st.session_state.get(
            "show_multi_insights",
            False
        )
        and accounts
    ):

        return

    st.header(
        "📊 Multi-Account Insights"
    )

    last_updated = st.session_state.get(
        "multi_stats_last_updated",
        "Not fetched yet"
    )

    st.caption(
        f"🕒 Last Updated: {last_updated}"
    )

    # -----------------------------------------------
    # REFRESH BUTTON
    # -----------------------------------------------
    if st.button(
        "🔄 Refresh Multi-Account Stats"
    ):

        refresh = True

        st.cache_data.clear()

    account_data = []

    # -----------------------------------------------
    # FETCH ACCOUNT DATA
    # -----------------------------------------------
    with st.spinner(
        "⏳ Fetching multi-account insights..."
    ):

        progress = st.progress(0)

        for index, email in enumerate(accounts):

            # ---------------------------------------
            # CACHE
            # ---------------------------------------
            if (
                email in multi_stats_cache
                and not refresh
            ):

                account_data.append(
                    multi_stats_cache[email]
                )

            else:

                stats = fetch_account_stats(
                    email=email,
                    scan_days=st.session_state.get(
                        "scan_days",
                        7
                    ),
                    email_limit=st.session_state.get(
                        "email_limit",
                        50
                    )
                )

                if stats:

                    multi_stats_cache[email] = stats

                    account_data.append(stats)

            progress.progress(
                (index + 1) / len(accounts)
            )

        progress.empty()

    # -----------------------------------------------
    # UPDATE STATE
    # -----------------------------------------------
    st.session_state.multi_stats_last_updated = (
        time.strftime(
            "%Y-%m-%d %I:%M %p"
        )
    )

    st.session_state.refresh_multi_stats = False

    # -----------------------------------------------
    # DISPLAY DATA
    # -----------------------------------------------
    if not account_data:

        st.info(
            "📭 No multi-account data available."
        )

        return

    df = pd.DataFrame(account_data)

    st.dataframe(
        df,
        use_container_width=True
    )

    # -----------------------------------------------
    # SUMMARY METRICS
    # -----------------------------------------------
    total_spam = df["SPAM"].sum()

    total_ham = df["HAM"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📁 Accounts",
        len(accounts)
    )

    col2.metric(
        "🚫 Total Spam",
        total_spam
    )

    col3.metric(
        "✅ Total Ham",
        total_ham
    )

    # -----------------------------------------------
    # CHART
    # -----------------------------------------------
    fig = px.bar(

        df,

        x="Email",

        y=["HAM", "SPAM"],

        title="📊 Spam vs HAM per Account",

        labels={
            "value": "Count",
            "variable": "Category"
        },

        barmode="stack"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -----------------------------------------------
    # SPAM RATIO
    # -----------------------------------------------
    if total_spam + total_ham > 0:

        spam_ratio = (
            total_spam
            / (total_spam + total_ham)
        )

        st.subheader(
            "📈 Overall Spam Ratio"
        )

        st.progress(spam_ratio)

        st.caption(
            f"Spam Percentage: "
            f"{round(spam_ratio * 100, 2)}%"
        )
