import streamlit as st


def setup_page(
    title: str,
    icon: str = "💰",
    layout: str = "wide",
) -> None:
    """
    Apply consistent page configuration.
    """
    st.set_page_config(
        page_title=f"{icon} {title}",
        page_icon=icon,
        layout=layout,
        initial_sidebar_state="collapsed",
    )


def show_app_header(
    title: str,
    subtitle: str | None = None,
) -> None:
    """
    Display a consistent application header.
    """
    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title">{title}</div>
            {f'<div class="app-subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def require_login() -> None:
    """
    Prevent access to application pages when the user is not logged in.
    """
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to continue.")
        st.stop()


def logout() -> None:
    """
    Clear the current login session.
    """
    for key in [
        "authenticated",
        "user_id",
        "username",
    ]:
        st.session_state.pop(key, None)

    st.rerun()


def show_sidebar() -> None:
    """
    Display the application sidebar/navigation.
    """
    if not st.session_state.get("authenticated", False):
        return

    with st.sidebar:
        st.markdown("### 💰 Expense Tracker")

        username = st.session_state.get("username", "")
        if username:
            st.caption(f"Logged in as **{username}**")

        st.divider()

        st.page_link(
            "app.py",
            label="Dashboard",
            icon="🏠",
        )

        st.page_link(
            "pages/02_Add_Transaction.py",
            label="Add Transaction",
            icon="➕",
        )

        st.page_link(
            "pages/03_Transaction_History.py",
            label="Transaction History",
            icon="📋",
        )

        st.page_link(
            "pages/04_Accounts.py",
            label="Accounts",
            icon="🏦",
        )

        st.page_link(
            "pages/05_Friends_Money.py",
            label="Friends' Money",
            icon="🤝",
        )

        st.page_link(
            "pages/06_Budgets.py",
            label="Budgets",
            icon="🎯",
        )

        st.page_link(
            "pages/07_Savings_Goals.py",
            label="Savings Goals",
            icon="💎",
        )

        st.page_link(
            "pages/08_Recurring_Transactions.py",
            label="Recurring",
            icon="🔄",
        )

        st.page_link(
            "pages/09_Reports.py",
            label="Reports",
            icon="📊",
        )

        st.page_link(
            "pages/10_Backup_Restore.py",
            label="Backup & Restore",
            icon="💾",
        )

        st.page_link(
            "pages/11_Settings.py",
            label="Settings",
            icon="⚙️",
        )

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True,
            type="secondary",
        ):
            logout()