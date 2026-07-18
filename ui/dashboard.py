# 📥 ui/dashboard.py

import math
import pandas as pd
import streamlit as st
import plotly.express as px
import html


# ---------------------------------------------------
# METRICS
# ---------------------------------------------------
def display_metrics(
    spam_emails,
    ham_emails
):

    st.subheader(
        "📊 Email Classification Summary"
    )

    total = (
        len(spam_emails)
        + len(ham_emails)
    )

    spam_percent = (
        round(
            len(spam_emails)
            / total
            * 100,
            1
        )
        if total
        else 0
    )

    ham_percent = (
        round(
            len(ham_emails)
            / total
            * 100,
            1
        )
        if total
        else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📬 Total Emails",
        total
    )

    col2.metric(
        "✅ HAM %",
        f"{ham_percent}%"
    )

    col3.metric(
        "🚫 SPAM %",
        f"{spam_percent}%"
    )


# ---------------------------------------------------
# PAGINATION HELPER
# ---------------------------------------------------
def paginate_data(
    data,
    page_size,
    page_number
):

    start = (
        (page_number - 1)
        * page_size
    )

    end = start + page_size

    return data[start:end]

# ---------------------------------------------------
# EMAIL VIEWER
# ---------------------------------------------------

def render_email_list(
    emails,
    label
):

    if not emails:
        st.info(f"No {label} emails available.")
        return

    # -----------------------------------------------
    # PAGINATION SETTINGS
    # -----------------------------------------------
    page_size_options = [10, 20, 50]

    col1, col2 = st.columns(2)

    with col1:
        page_size = st.selectbox(
            "Emails Per Page",
            page_size_options,
            index=1,
            key=f"{label}_page_size"
        )

    total_pages = math.ceil(len(emails) / page_size)

    with col2:
        page_number = st.number_input(
            "Page",
            min_value=1,
            max_value=max(total_pages, 1),
            value=1,
            step=1,
            key=f"{label}_page_number"
        )

    # -----------------------------------------------
    # PAGINATED EMAILS
    # -----------------------------------------------
    paginated_emails = paginate_data(
        emails,
        page_size,
        page_number
    )

    st.caption(f"Showing {len(paginated_emails)} of {len(emails)} emails")

    # -----------------------------------------------
    # MODERN CARD UI (STABLE VERSION)
    # -----------------------------------------------
    for email in paginated_emails:

        confidence = email.get("confidence", 0)
        risk = email.get("risk", "LOW")
        score = email.get("risk_score", 0)

        # CARD SEPARATOR
        st.markdown("---")

        # ---------------------------------------
        # HEADER
        # ---------------------------------------
        col1, col2 = st.columns([5, 1])

        with col1:
            st.markdown(f"### 📧 {email['subject']}")
            st.markdown(
                f"<span style='color:#9ca3af; font-size:13px;'>"
                f"{email['sender']} → {email['recipient']}"
                f"</span>",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"<div style='text-align:right; color:#9ca3af; font-size:12px;'>"
                f"{email['time']}</div>",
                unsafe_allow_html=True
            )

        # ---------------------------------------
        # BADGES (COMPACT)
        # ---------------------------------------
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"**Confidence:** `{confidence}%`")

        with col2:
            st.markdown("✅ HAM" if label == "HAM" else "🚫 SPAM")

        with col3:
            if risk == "HIGH":
                st.markdown(f"🔴 Risk ({score})")
            elif risk == "MEDIUM":
                st.markdown(f"🟡 Risk ({score})")
            else:
                st.markdown(f"🟢 Safe ({score})")

        # ---------------------------------------
        # WHY FLAGGED
        # ---------------------------------------
        reasons = email.get("phishing_reasons", "")

        if reasons:
            with st.expander("⚠ Why flagged"):
                for r in str(reasons).split(","):
                    st.write(f"- {r.strip()}")

        # ---------------------------------------
        # CONTENT BOX
        # ---------------------------------------
        st.markdown("#### 📄 Email Content")

        st.markdown(
            f"""
            <div style="
                background-color:#1e2228;
                padding:18px;
                border-radius:12px;
                border:1px solid #333;
                font-size:14px;
                line-height:1.6;
                max-height:250px;
                overflow:auto;
            ">
            {html.escape(email['content'])}
            </div>
            """,
            unsafe_allow_html=True
        )


# def render_email_list(
#     emails,
#     label
# ):

#     if not emails:

#         st.info(
#             f"No {label} emails available."
#         )

#         return

#     # -----------------------------------------------
#     # PAGINATION SETTINGS
#     # -----------------------------------------------
#     page_size_options = [
#         10,
#         20,
#         50
#     ]

#     col1, col2 = st.columns(2)

#     with col1:

#         page_size = st.selectbox(
#             "Emails Per Page",
#             page_size_options,
#             index=1,
#             key=f"{label}_page_size"
#         )

#     total_pages = math.ceil(
#         len(emails) / page_size
#     )

#     with col2:

#         page_number = st.number_input(
#             "Page",
#             min_value=1,
#             max_value=max(total_pages, 1),
#             value=1,
#             step=1,
#             key=f"{label}_page_number"
#         )

#     # -----------------------------------------------
#     # PAGINATED EMAILS
#     # -----------------------------------------------
#     paginated_emails = paginate_data(
#         emails,
#         page_size,
#         page_number
#     )

#     st.caption(
#         f"Showing "
#         f"{len(paginated_emails)} "
#         f"of {len(emails)} emails"
#     )

#     # -----------------------------------------------
#     # MODERN CARD UI
#     # -----------------------------------------------
#     for email in paginated_emails:

#         confidence = email.get("confidence", 0)
#         risk = email.get("risk", "LOW")
#         score = email.get("risk_score", 0)

#         st.markdown(
#             """
#             <div style="
#                 background-color:#111418;
#                 padding:20px;
#                 border-radius:14px;
#                 border:1px solid #2a2f36;
#                 margin-bottom:20px;
#             ">
#             """,
#             unsafe_allow_html=True
#         )

#         # ---------------------------------------
#         # HEADER
#         # ---------------------------------------
#         col1, col2 = st.columns([5, 1])

#         with col1:
#             st.markdown(f"### 📧 {email['subject']}")
#             st.markdown(
#                 f"""
#                 <span style='color:#9ca3af; font-size:13px;'>
#                 {email['sender']} → {email['recipient']}
#                 </span> """,
#                 unsafe_allow_html=True
#                 )

#         with col2:
#             st.markdown(
#                 f"""
#                 <div style='text-align:right; color:#9ca3af; font-size:12px;'>
#                 {email['time']} </div> """,
#                 unsafe_allow_html=True
#                 )

#         # ---------------------------------------
#         # BADGES
#         # ---------------------------------------
#         col1, col2, col3 = st.columns(3)

#         with col1:
#             # st.metric("Confidence", f"{confidence}%")
#             st.markdown(f"**Confidence:** `{confidence}%`")

#         with col2:
#             if label == "HAM":
#                 st.markdown("✅ HAM")
#             else:
#                 st.markdown("🚫 SPAM")

#         with col3:
#             if risk == "HIGH":
#                 st.markdown(f"🔴 Risk ({score})")
#             elif risk == "MEDIUM":
#                 st.markdown(f"🟡 Risk ({score})")
#             else:
#                 st.markdown(f"🟢 Safe ({score})")

#         # ---------------------------------------
#         # WHY FLAGGED
#         # ---------------------------------------
#         reasons = email.get("phishing_reasons", "")

#         if reasons:
#             with st.expander("⚠ Why flagged"):
#                 for r in str(reasons).split(","):
#                     st.write(f"- {r.strip()}")

#         # ---------------------------------------
#         # CONTENT BOX
#         # ---------------------------------------
#         st.markdown("#### 📄 Email Content")

#         st.markdown(
#             f"""
#             <div style="
#                 background-color:#1e2228;
#                 padding:18px;
#                 border-radius:12px;
#                 border:1px solid #333;
#                 font-size:14px;
#                 line-height:1.6;
#                 max-height:250px;
#                 overflow:auto;
#             ">
#             {html.escape(email['content'])}
#             </div>
#             """,
#             unsafe_allow_html=True
#         )

#         st.markdown("</div>", unsafe_allow_html=True)
#         st.markdown("<br>", unsafe_allow_html=True)
# ---------------------------------------------------
# EMAIL TABS
# ---------------------------------------------------
def display_email_tabs(
    spam_emails,
    ham_emails
):

    st.subheader(
        "📂 Classified Emails"
    )

    tabs = st.tabs([

        f"✅ HAM Emails ({len(ham_emails)})",

        f"🚫 SPAM Emails ({len(spam_emails)})"

    ])

    with tabs[0]:

        render_email_list(
            ham_emails,
            "HAM"
        )

    with tabs[1]:

        render_email_list(
            spam_emails,
            "SPAM"
        )


# ---------------------------------------------------
# CHART
# ---------------------------------------------------
def display_chart(
    spam_emails,
    ham_emails
):

    df = pd.DataFrame({

        "Label": [

            "HAM",
            "SPAM"

        ],

        "Count": [

            len(ham_emails),

            len(spam_emails)

        ]

    })

    fig = px.pie(

        df,

        names="Label",

        values="Count",

        title="📊 Email Classification",

        hole=0.4
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# import math
# import pandas as pd
# import streamlit as st
# import plotly.express as px


# # ---------------------------------------------------
# # METRICS
# # ---------------------------------------------------
# def display_metrics(
#     spam_emails,
#     ham_emails
# ):

#     st.subheader(
#         "📊 Email Classification Summary"
#     )

#     total = (
#         len(spam_emails)
#         + len(ham_emails)
#     )

#     spam_percent = (
#         round(
#             len(spam_emails)
#             / total
#             * 100,
#             1
#         )
#         if total
#         else 0
#     )

#     ham_percent = (
#         round(
#             len(ham_emails)
#             / total
#             * 100,
#             1
#         )
#         if total
#         else 0
#     )

#     col1, col2, col3 = st.columns(3)

#     col1.metric(
#         "📬 Total Emails",
#         total
#     )

#     col2.metric(
#         "✅ HAM %",
#         f"{ham_percent}%"
#     )

#     col3.metric(
#         "🚫 SPAM %",
#         f"{spam_percent}%"
#     )


# # ---------------------------------------------------
# # PAGINATION HELPER
# # ---------------------------------------------------
# def paginate_data(
#     data,
#     page_size,
#     page_number
# ):

#     start = (
#         (page_number - 1)
#         * page_size
#     )

#     end = start + page_size

#     return data[start:end]


# # ---------------------------------------------------
# # EMAIL VIEWER
# # ---------------------------------------------------
# def render_email_list(
#     emails,
#     label
# ):

#     if not emails:

#         st.info(
#             f"No {label} emails available."
#         )

#         return

#     # -----------------------------------------------
#     # PAGINATION SETTINGS
#     # -----------------------------------------------
#     page_size_options = [
#         10,
#         20,
#         50
#     ]

#     col1, col2 = st.columns(2)

#     with col1:

#         page_size = st.selectbox(
#             "Emails Per Page",
#             page_size_options,
#             index=1,
#             key=f"{label}_page_size"
#         )

#     total_pages = math.ceil(
#         len(emails) / page_size
#     )

#     with col2:

#         page_number = st.number_input(
#             "Page",
#             min_value=1,
#             max_value=max(total_pages, 1),
#             value=1,
#             step=1,
#             key=f"{label}_page_number"
#         )

#     # -----------------------------------------------
#     # PAGINATED EMAILS
#     # -----------------------------------------------
#     paginated_emails = paginate_data(
#         emails,
#         page_size,
#         page_number
#     )

#     st.caption(
#         f"Showing "
#         f"{len(paginated_emails)} "
#         f"of {len(emails)} emails"
#     )

#     # -----------------------------------------------
#     # RENDER EMAILS
#     # -----------------------------------------------
#     for email in paginated_emails:

#         confidence = email.get(
#             "confidence",
#             0
#         )

#         with st.expander(

#             f"📧 "
#             f"{email['subject']} "
#             f"— "
#             f"{email['time']}"

#         ):

#             # ---------------------------------------
#             # EMAIL META
#             # ---------------------------------------
#             st.markdown(

#                 f"""
#                 **From:** `{email['sender']}`

#                 **To:** `{email['recipient']}`

#                 **Confidence:** `{confidence}%`

#                 **Prediction:**
#                 {"🟢 HAM" if label == "HAM" else "🔴 SPAM"}
#                 """
#             )

#             # CONTENT
#             # ---------------------------------------
#             st.text_area(
#                 "Email Content",
#                 value=email["content"],
#                 height=250,
#                 disabled=True,
#                 key=( f"email_content_" f"{email.get('id', '')}_" f"{hash(email['subject'] + email['time'])}" )
#             )


# # ---------------------------------------------------
# # EMAIL TABS
# # ---------------------------------------------------
# def display_email_tabs(
#     spam_emails,
#     ham_emails
# ):

#     st.subheader(
#         "📂 Classified Emails"
#     )

#     tabs = st.tabs([

#         f"✅ HAM Emails ({len(ham_emails)})",

#         f"🚫 SPAM Emails ({len(spam_emails)})"

#     ])

#     # -----------------------------------------------
#     # HAM TAB
#     # -----------------------------------------------
#     with tabs[0]:

#         render_email_list(
#             ham_emails,
#             "HAM"
#         )

#     # -----------------------------------------------
#     # SPAM TAB
#     # -----------------------------------------------
#     with tabs[1]:

#         render_email_list(
#             spam_emails,
#             "SPAM"
#         )


# # ---------------------------------------------------
# # CHART
# # ---------------------------------------------------
# def display_chart(
#     spam_emails,
#     ham_emails
# ):

#     df = pd.DataFrame({

#         "Label": [

#             "HAM",
#             "SPAM"

#         ],

#         "Count": [

#             len(ham_emails),

#             len(spam_emails)

#         ]

#     })

#     fig = px.pie(

#         df,

#         names="Label",

#         values="Count",

#         title="📊 Email Classification",

#         hole=0.4
#     )

#     st.plotly_chart(
#         fig,
#         use_container_width=True
#     )
