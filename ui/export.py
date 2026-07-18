# 💾 ui/export.py

import pandas as pd
import streamlit as st


# ---------------------------------------------------
# CACHE CSV CONVERSION
# ---------------------------------------------------
@st.cache_data
def convert_df_to_csv(df):

    return df.to_csv(
        index=False
    ).encode("utf-8")


# ---------------------------------------------------
# EXPORT BUTTONS
# ---------------------------------------------------
def export_buttons(
    spam_emails,
    ham_emails
):

    st.markdown(
        "### 💾 Export Classified Emails"
    )

    col1, col2, col3 = st.columns(3)

    # -----------------------------------------------
    # HAM EXPORT
    # -----------------------------------------------
    with col1:

        if ham_emails:

            ham_df = pd.DataFrame(
                ham_emails
            )

            ham_csv = convert_df_to_csv(
                ham_df
            )

            st.download_button(

                label=(
                    f"✅ Download HAM "
                    f"({len(ham_emails)})"
                ),

                data=ham_csv,

                file_name="ham_emails.csv",

                mime="text/csv",

                use_container_width=True,

                help=(
                    "Download all "
                    "non-spam emails"
                )
            )

        else:

            st.info(
                "✅ No HAM emails."
            )

    # -----------------------------------------------
    # SPAM EXPORT
    # -----------------------------------------------
    with col2:

        if spam_emails:

            spam_df = pd.DataFrame(
                spam_emails
            )

            spam_csv = convert_df_to_csv(
                spam_df
            )

            st.download_button(

                label=(
                    f"🚫 Download SPAM "
                    f"({len(spam_emails)})"
                ),

                data=spam_csv,

                file_name="spam_emails.csv",

                mime="text/csv",

                use_container_width=True,

                help=(
                    "Download all "
                    "spam emails"
                )
            )

        else:

            st.info(
                "🚫 No SPAM emails."
            )

    # -----------------------------------------------
    # COMBINED EXPORT
    # -----------------------------------------------
    with col3:

        if spam_emails or ham_emails:

            combined_df = pd.concat(

                [

                    pd.DataFrame(
                        ham_emails
                    ),

                    pd.DataFrame(
                        spam_emails
                    )

                ],

                ignore_index=True

            )

            combined_csv = convert_df_to_csv(
                combined_df
            )

            st.download_button(

                label=(
                    "⬇️ Download "
                    "Summary CSV"
                ),

                data=combined_csv,

                file_name="email_summary.csv",

                mime="text/csv",

                use_container_width=True,

                help=(
                    "Download all "
                    "classified emails"
                )
            )

        else:

            st.info(
                "📭 No emails to export."
            )
