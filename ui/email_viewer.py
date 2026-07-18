# 🧾 ui/email_viewer.py

import streamlit as st

def render_email_tabs(spam_emails, ham_emails):
    st.subheader("📂 Classified Emails")
    tabs = st.tabs([
        f"✅ HAM Emails ({len(ham_emails)})",
        f"🚫 SPAM Emails ({len(spam_emails)})"
    ])

    for idx, (emails, label) in enumerate([(ham_emails, "HAM"), (spam_emails, "SPAM")]):
        with tabs[idx]:
            if not emails:
                st.info(f"No {label} emails to display.")
                continue

            for email in emails:
                with st.expander(f"📧 {email['subject']} — {email['time']}"):
                    st.markdown(f"""
                        **From:** `{email['sender']}`
                        **To:** `{email['recipient']}`
                        **Confidence:** **{email['confidence']}%**
                        **Prediction:** {"🟢" if label == "HAM" else "🔴"} `{label}`
                    """)
                    st.code(email['content'], language="text")
