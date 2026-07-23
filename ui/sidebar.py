# 📊 ui/sidebar.py
import os
import shutil
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import time as _time

from auth import (
    load_account_service,
    logout as auth_logout,
    clear_session
)
from oauth_google import login_google
# from utils.session import (
#     initialize_session_state
# )

from utils.session import get_accounts_for_device
from utils.token_utils import (
    remove_readonly
)

# ---------------------------------------------------
# INITIALIZE SESSION
# ---------------------------------------------------
# initialize_session_state()


# ===================================================
# CACHE LOGO
# ===================================================
@st.cache_data
def load_logo():

    return "assets/app_logo.png"


# ===================================================
# SAFE INDEX HELPER
# ===================================================
def safe_index(options, value, default):

    try:

        return options.index(value)

    except Exception:

        return options.index(default)

# ===================================================
# LOGIN EXISTING ACCOUNT (saved token, no OAuth popup)
# ===================================================
def login_account(email):
    """
    Logs back into an account that already has a saved
    token.json (refreshing it if needed). This does NOT
    handle brand-new logins — those go through
    login_button() instead, since a fresh Google login
    requires the OAuth2Component popup, not a plain button
    click.
    """

    try:

        st.session_state.email = email

        with st.spinner("🔐 Connecting Gmail..."):

            service = load_account_service(email)

        # -------------------------------------------
        # VALID SERVICE
        # -------------------------------------------
        if service:

            st.session_state.service = service

            st.session_state.logged_in = True

            st.session_state.fetch_on_login = True

            st.session_state.fetching_in_progress = False

            st.session_state.timeout_handled = False

            st.session_state.session_timed_out = False

            st.session_state.show_login_prompt = False

            st.session_state.last_active = datetime.now()

            # ---------------------------------------
            # RESET FLAGS
            # ---------------------------------------
            st.session_state.logout_triggered = False

            st.session_state.switching_account = False

            st.session_state.auto_login_checked = False

            # ---------------------------------------
            # CLEAR OLD EMAIL DATA
            # ---------------------------------------
            st.session_state.spam_emails = []

            st.session_state.ham_emails = []

            st.session_state.sender_count = {}

            st.session_state.recipient_count = {}

            # ---------------------------------------
            # SUCCESS
            # ---------------------------------------
            st.toast(
                "✅ Gmail Connected Successfully"
            )

            st.rerun()

        else:

            st.error(
                "❌ Failed to connect Gmail."
            )

        return False

    except Exception as e:

        st.sidebar.error(
            f"❌ Login Failed: {e}"
        )

        return False


# ===================================================
# LOGOUT
# ===================================================
def handle_logout():

    # -----------------------------------------------
    # FLAGS
    # -----------------------------------------------
    st.session_state.logout_triggered = True

    st.session_state.switching_account = False

    st.session_state.auto_login_checked = True

    # -----------------------------------------------
    # REVOKE TOKEN + CLEAR SESSION
    # remember_me=True keeps token.json on disk so
    # auto_login() can silently sign back in on the
    # NEXT app visit; it does not affect this session,
    # which stays logged out until the user logs in again.
    # -----------------------------------------------
    auth_logout(remember_me=True)

    st.toast("👋 Logged out successfully")

    st.rerun()


# ===================================================
# SWITCH ACCOUNT
# ===================================================
def handle_switch_account():

    # -----------------------------------------------
    # FLAGS
    # -----------------------------------------------
    st.session_state.switching_account = True

    st.session_state.logout_triggered = False

    st.session_state.auto_login_checked = True

    # -----------------------------------------------
    # CLEAR CURRENT SESSION
    # -----------------------------------------------
    clear_session()

    st.toast("🔄 Switch account")

    st.rerun()


# ===================================================
# DELETE TOKENS
# ===================================================
def delete_all_tokens():

    try:

        if os.path.exists("tokens"):

            shutil.rmtree(
                "tokens",
                onerror=remove_readonly
            )

            os.makedirs(
                "tokens",
                exist_ok=True
            )

        clear_session(
            keys=[
                "accounts",
                "email",
                "logged_in",
                "service",
                "user_id"
            ]
        )

        st.success(
            "✅ All Gmail accounts removed."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"❌ Failed to delete tokens: {e}"
        )


# ===================================================
# ACCOUNT CARD
# ===================================================
def render_account_card():

    st.success("✅ Active Gmail Account")

    st.markdown(
        f"""
        ### 👤 {st.session_state.get('user_id', '')}

        📧 **{st.session_state.get('email', '')}**
        """
    )

    if st.session_state.get("last_active"):

        st.caption(
            f"🕒 Last Active: "
            f"{st.session_state.last_active.strftime('%Y-%m-%d %I:%M %p')}"
        )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔄 Switch",
            use_container_width=True
        ):

            handle_switch_account()

    with col2:

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            handle_logout()


# ===================================================
# LOGIN PANEL
# ===================================================

def render_login_panel():

    accounts = st.session_state.get(
        "accounts",
        []
    )

    st.markdown(
        "### 👥 Gmail Accounts"
    )

    show_oauth_button = False
    button_text = "Connect First Gmail Account"

    # -----------------------------------------------
    # EXISTING ACCOUNTS
    # -----------------------------------------------
    if accounts:

        selected_account = st.selectbox(
            "📂 Select Account",
            accounts + ["➕ Add New Gmail"],
            key="account_selector"
        )

        if selected_account != "➕ Add New Gmail":

            if st.button(
                "🔐 Login",
                use_container_width=True
            ):
                login_account(selected_account)

        else:
            show_oauth_button = True
            button_text = "Connect Gmail"

    # -----------------------------------------------
    # FIRST LOGIN — polished empty state
    # -----------------------------------------------
    else:

        st.markdown(
            """
            <style>
            .ms-empty-card {
                background: linear-gradient(180deg, rgba(79,124,255,0.08), rgba(139,92,246,0.04));
                border: 1px solid rgba(139, 109, 255, 0.25);
                border-radius: 16px;
                padding: 26px 18px 20px 18px;
                text-align: center;
                margin-bottom: 6px;
            }
            .ms-empty-icon {
                width: 48px;
                height: 48px;
                margin: 0 auto 12px auto;
                border-radius: 13px;
                background: linear-gradient(135deg, #4F7CFF, #8B5CF6);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 23px;
                box-shadow: 0 6px 16px rgba(99, 73, 255, 0.35);
            }
            .ms-empty-title {
                font-size: 14.5px;
                font-weight: 600;
                color: rgba(255,255,255,0.92);
                margin-bottom: 4px;
            }
            .ms-empty-sub {
                font-size: 12px;
                color: rgba(255,255,255,0.5);
                line-height: 1.5;
                margin: 0;
            }
            </style>

            <div class="ms-empty-card">
                <div class="ms-empty-icon">🛡️</div>
                <div class="ms-empty-title">No Gmail account connected</div>
                <p class="ms-empty-sub">Connect an account to start scanning for spam.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        show_oauth_button = True

    # -----------------------------------------------
    # OAUTH POPUP BUTTON
    # -----------------------------------------------
    if show_oauth_button:

        auth_url = login_google()

        components.html(
    f"""
    <style>
    .ms-connect-btn {{
        width: 100%;
        padding: 0.6rem 0.8rem;
        background: linear-gradient(135deg, #4F7CFF, #8B5CF6);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.85rem;
        line-height: 1.3;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(99, 73, 255, 0.3);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        white-space: normal;
        word-wrap: break-word;
    }}
    .ms-connect-btn:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(99, 73, 255, 0.4);
    }}
    </style>
    <button class="ms-connect-btn" onclick="
        var w = 500, h = 600;
        var left = (screen.width/2) - (w/2);
        var top = (screen.height/2) - (h/2);
        window.open(
            '{auth_url}',
            'mailshield_oauth',
            'width=' + w + ',height=' + h + ',top=' + top + ',left=' + left + ',resizable=yes,scrollbars=yes'
        );
        window.parent.postMessage({{type: 'mailshield_oauth_opened'}}, '*');
    ">
        🔐 {button_text}
    </button>
    """,
    height=72,
)

    


        st.markdown(
            """
            <p style="font-size: 11px; color: rgba(255,255,255,0.4); text-align:center; margin: 4px 0 12px 0;">
            Opens a small window for Google sign-in
            </p>
            """,
            unsafe_allow_html=True,
        )

        if st.button("↻  I've finished signing in", use_container_width=True):
            device_id = st.session_state.get("device_id")

            st.write("DEBUG device_id:", device_id)

            from utils.session import get_accounts_for_device, get_most_recent_account
            found_accounts = get_accounts_for_device(device_id)

            st.write("DEBUG accounts found on disk:", found_accounts)

            st.session_state["accounts"] = found_accounts

            newest_email = get_most_recent_account(device_id)

            st.write("DEBUG newest_email:", newest_email)
            st.stop() 

            if newest_email:
                login_account(newest_email)
            else:
                st.rerun()

        # if st.button("↻  I've finished signing in", use_container_width=True):
        #     device_id = st.session_state.get("device_id")

        #     from utils.session import get_accounts_for_device, get_most_recent_account
        #     st.session_state["accounts"] = get_accounts_for_device(device_id)

        #     newest_email = get_most_recent_account(device_id)

        #     if newest_email:
        #         login_account(newest_email)
        #     else:
        #         st.rerun()
# ===================================================
# SESSION EXPIRED PANEL
# ===================================================
def render_session_expired():

    st.warning(
        "⏳ Session expired. Please login again."
    )

    accounts = st.session_state.get(
        "accounts",
        []
    )

    if accounts:

        selected = st.selectbox(
            "🔐 Select Account",
            accounts,
            key="expired_session_account"
        )

        if st.button(
            "🔐 Re-Login",
            use_container_width=True
        ):

            login_account(selected)


# ===================================================
# QUICK STATS
# ===================================================
def render_quick_stats():

    st.markdown("### 📊 Quick Stats")

    col1, col2 = st.columns(2)

    col1.metric(
        "📁 Accounts",
        len(
            st.session_state.get(
                "accounts",
                []
            )
        )
    )

    col2.metric(
        "🔄 Total Scans",
        st.session_state.get(
            "fetch_count",
            0
        )
    )

    # -----------------------------------------------
    # LAST FETCH
    # -----------------------------------------------
    last_fetch = st.session_state.get(
        "last_fetch_time"
    )

    if last_fetch:

        st.caption(
            f"🕒 Last Scan: "
            f"{last_fetch.strftime('%Y-%m-%d %I:%M %p')}"
        )


# ===================================================
# MULTI ACCOUNT SETTINGS
# ===================================================
def render_multi_account_settings():

    if len(
        st.session_state.get(
            "accounts",
            []
        )
    ) > 1:

        st.checkbox(
            "📊 Multi-Account Insights",
            value=st.session_state.get(
                "show_multi_insights",
                False
            ),
            key="show_multi_insights"
        )


# ===================================================
# SCAN SETTINGS
# ===================================================
def render_scan_settings():

    st.markdown("### ⚙️ Scan Settings")

    # -----------------------------------------------
    # DAYS
    # -----------------------------------------------
    day_options = [1, 3, 7, 30]

    st.selectbox(
        "📅 Scan Emails From",
        options=day_options,
        index=safe_index(
            day_options,
            st.session_state.get(
                "scan_days",
                7
            ),
            7
        ),
        format_func=lambda x:
            f"Last {x} day{'s' if x > 1 else ''}",
        key="scan_days"
    )

    # -----------------------------------------------
    # LIMIT
    # -----------------------------------------------
    limit_options = [25, 50, 100, 200]

    st.selectbox(
        "📨 Max Emails",
        options=limit_options,
        index=safe_index(
            limit_options,
            st.session_state.get(
                "email_limit",
                100
            ),
            100
        ),
        key="email_limit"
    )

    # -----------------------------------------------
    # LABELS
    # -----------------------------------------------
    st.checkbox(
        "🏷️ Auto Label Emails",
        value=st.session_state.get(
            "label_emails",
            True
        ),
        key="label_emails"
    )

    # -----------------------------------------------
    # AUTO FETCH
    # -----------------------------------------------
    st.checkbox(
        "⚡ Auto Fetch After Login",
        value=st.session_state.get(
            "auto_fetch_toggle",
            True
        ),
        key="auto_fetch_toggle"
    )


# ===================================================
# DEVELOPER OPTIONS
# ===================================================
def render_developer_options():

    st.markdown("### 🛠️ Developer Options")

    st.caption(
        "Danger Zone"
    )

    confirm = st.checkbox(
        "I understand this action"
    )

    if (
        confirm
        and st.button(
            "🗑️ Delete All Tokens",
            use_container_width=True
        )
    ):

        delete_all_tokens()

    # -----------------------------------------------
    # CLEAR CACHE
    # -----------------------------------------------
    if st.button(
        "🧹 Clear App Cache",
        use_container_width=True
    ):

        st.cache_data.clear()

        st.cache_resource.clear()

        st.success(
            "✅ Cache Cleared"
        )

    # -----------------------------------------------
    # CLEAR DATABASE
    # -----------------------------------------------
    if st.button("🗑️ Reset Database", use_container_width=True):

        from database.db import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM email_scans")
        cursor.execute("DELETE FROM scan_state")

        conn.commit()
        conn.close()

        st.success("✅ Database cleared successfully")
        # reset session too
        st.session_state.spam_emails = []
        st.session_state.ham_emails = []

        st.rerun()

# ===================================================
# MAIN SIDEBAR
# ===================================================
def render_sidebar():

    # =================================================
    # LOGO
    # =================================================
    st.sidebar.image(
        load_logo(),
        width=140
    )

    st.sidebar.markdown(
        "# 💌 MailShield"
    )

    st.sidebar.caption(
        "AI Powered Gmail Security"
    )

    st.sidebar.markdown("---")

    # =================================================
    # ACCOUNT SECTION
    # =================================================
    with st.sidebar.container():

        if st.session_state.get(
            "logged_in",
            False
        ):

            render_account_card()

        else:

            if st.session_state.get(
                "session_timed_out",
                False
            ):

                render_session_expired()

            else:

                render_login_panel()

    st.sidebar.markdown("---")

    # =================================================
    # QUICK STATS
    # =================================================
    with st.sidebar.expander(
        "📊 Insights",
        expanded=True
    ):

        render_quick_stats()

        render_multi_account_settings()

    # =================================================
    # SCAN SETTINGS
    # =================================================
    with st.sidebar.expander(
        "⚙️ Settings",
        expanded=False
    ):

        render_scan_settings()

    # =================================================
    # DEVELOPER OPTIONS
    # =================================================
    with st.sidebar.expander(
        "🛠️ Developer",
        expanded=False
    ):

        render_developer_options()

    # =================================================
    # FOOTER
    # =================================================
    st.sidebar.markdown("---")

    st.sidebar.caption(
        "© 2026 MailShield • VGEC"
    )

    return st.session_state.get(
        "show_multi_insights",
        False
    )
