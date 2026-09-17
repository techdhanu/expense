import streamlit as st


# =========================================================
# PAGE SETUP
# =========================================================

def setup_page(
    title: str,
    icon: str = "💰",
    layout: str = "wide",
) -> None:
    """
    Configure common Streamlit page settings.

    Authenticated pages automatically receive
    the application navigation.
    """

    st.set_page_config(
        page_title=f"{icon} {title}",
        page_icon=icon,
        layout=layout,
        initial_sidebar_state="collapsed",
    )

    # Show application navigation for authenticated pages.
    if (
        title.lower() != "login"
        and st.session_state.get("authenticated", False)
    ):
        show_sidebar()


# =========================================================
# APP HEADER
# =========================================================

def show_app_header(
    title: str,
    subtitle: str | None = None,
) -> None:
    """Display a consistent application header."""

    subtitle_html = (
        f'<div class="app-subtitle">{subtitle}</div>'
        if subtitle
        else ""
    )

    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# AUTHENTICATION
# =========================================================

def require_login() -> None:
    """
    Prevent unauthenticated users from accessing
    protected pages.
    """

    if st.session_state.get("authenticated", False):
        return

    st.markdown(
        """
        <div style="
            max-width: 500px;
            margin: 80px auto 20px auto;
            text-align: center;
        ">
            <div style="font-size: 64px;">🔐</div>
            <h2>Login Required</h2>
            <p style="color: #9ca3af;">
                Please log in to access your expense tracker.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link(
        "app.py",
        label="🔑 Go to Login",
        icon="🔐",
    )

    st.stop()


# =========================================================
# LOGOUT
# =========================================================

def logout() -> None:
    """Clear authentication-related session state."""

    for key in [
        "authenticated",
        "user_id",
        "username",
    ]:
        st.session_state.pop(
            key,
            None,
        )

    st.switch_page("app.py")


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

def show_sidebar() -> None:
    """Display application navigation in the sidebar."""

    with st.sidebar:

        st.markdown(
            "## 💰 Expense Tracker"
        )

        username = st.session_state.get(
            "username"
        )

        if username:

            st.caption(
                f"Logged in as: **{username}**"
            )

        st.divider()

        # -------------------------------------------------
        # MAIN
        # -------------------------------------------------

        st.page_link(
            "pages/Dashboard.py",
            label="Dashboard",
            icon="🏠",
        )

        st.page_link(
            "pages/Add_transaction.py",
            label="Add Transaction",
            icon="➕",
        )

        st.page_link(
            "pages/Transaction_History.py",
            label="Transaction History",
            icon="📋",
        )

        st.page_link(
            "pages/accounts.py",
            label="Accounts",
            icon="🏦",
        )

        st.page_link(
            "pages/friends_money.py",
            label="Friends' Money",
            icon="👥",
        )

        # -------------------------------------------------
        # PLANNING
        # -------------------------------------------------

        st.divider()

        st.page_link(
            "pages/budgets.py",
            label="Budgets",
            icon="💰",
        )

        st.page_link(
            "pages/savings_goal.py",
            label="Savings Goals",
            icon="🎯",
        )

        st.page_link(
            "pages/recurring_transactions.py",
            label="Recurring Transactions",
            icon="🔄",
        )

        st.page_link(
            "pages/reports.py",
            label="Reports",
            icon="📊",
        )

        # -------------------------------------------------
        # SYSTEM
        # -------------------------------------------------

        st.divider()

        st.page_link(
            "pages/backup_restore.py",
            label="Backup & Restore",
            icon="💾",
        )

        st.page_link(
            "pages/settings.py",
            label="Settings",
            icon="⚙️",
        )

        # -------------------------------------------------
        # LOGOUT
        # -------------------------------------------------

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):
            logout()