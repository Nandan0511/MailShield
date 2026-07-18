# 📈 ui/analytics.py

import pandas as pd
import streamlit as st
import plotly.express as px

from database.queries import (

    get_recent_scans,

    get_account_stats,

    get_spam_trend,

    search_emails
)


# ---------------------------------------------------
# ANALYTICS DASHBOARD
# ---------------------------------------------------
def render_analytics_dashboard():

    current_email = st.session_state.get(
        "email",
        ""
    )

    if not current_email:

        return

    st.header(
        "📈 Historical Analytics"
    )

    # -----------------------------------------------
    # LOAD ACCOUNT DATA
    # -----------------------------------------------
    recent_scans = get_recent_scans(
        current_email
    )

    if not recent_scans:

        st.info(
            "📭 No historical scan data available yet."
        )

        return

    df = pd.DataFrame(recent_scans)

    # -----------------------------------------------
    # SUMMARY METRICS
    # -----------------------------------------------
    total_scans = len(df)

    spam_count = len(

        df[
            df["prediction"] == "🚫 SPAM"
        ]
    )

    ham_count = len(

        df[
            df["prediction"] == "✅ HAM"
        ]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📬 Total Stored Emails",
        total_scans
    )

    col2.metric(
        "✅ Total Ham",
        ham_count
    )

    col3.metric(
        "🚫 Total Spam",
        spam_count
    )

    st.markdown("---")

    # -----------------------------------------------
    # SEARCH SYSTEM
    # -----------------------------------------------
    st.subheader(
        "🔍 Search Historical Emails"
    )

    keyword = st.text_input(
        "Search by subject, sender, recipient, prediction..."
    )

    if keyword:

        results = search_emails(
            keyword,
            current_email
        )

        if results:

            search_df = pd.DataFrame(results)

            st.dataframe(
                search_df,
                use_container_width=True
            )

        else:

            st.warning(
                "No matching emails found."
            )

    st.markdown("---")

    # -----------------------------------------------
    # ACCOUNT ANALYTICS
    # -----------------------------------------------
    st.subheader(
        "📊 Account Analytics"
    )

    stats = get_account_stats(
        current_email
    )

    if stats:

        stats_df = pd.DataFrame(stats)

        # NOTE: get_account_stats() is scoped to a single
        # account (current_email), so grouping by
        # account_email always produces one bar group. Chart
        # by prediction instead so the breakdown is actually
        # meaningful for this account.
        fig = px.bar(

            stats_df,

            x="prediction",

            y="total",

            color="prediction",

            title=f"Spam vs HAM — {current_email}"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("---")

    # -----------------------------------------------
    # SPAM TREND
    # -----------------------------------------------
    st.subheader(
        "📈 Spam Trend"
    )

    trend_data = get_spam_trend(
        current_email
    )

    if trend_data:

        trend_df = pd.DataFrame(
            trend_data
        )

        trend_fig = px.line(

            trend_df,

            x="scan_time",

            y="spam_count",

            markers=True,

            title="Spam Detection Trend"
        )

        st.plotly_chart(
            trend_fig,
            use_container_width=True
        )

    st.markdown("---")

    # -----------------------------------------------
    # RECENT SCANS
    # -----------------------------------------------
    st.subheader(
        "🕒 Recent Scan History"
    )

    st.dataframe(
        df.head(50),
        use_container_width=True
    )
