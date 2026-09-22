import streamlit as st

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
    logout,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Settings",
    "⚙️",
    "wide",
)

require_login()


# =========================================================
# PAGE HEADER
# =========================================================

show_app_header(
    "Settings",
    "Manage your application preferences and account session.",
)


# =========================================================
# APPLICATION SETTINGS
# =========================================================

st.markdown("## ⚙️ Application Settings")

st.caption(
    "Configure your application preferences and review "
    "important account and security information."
)


# =========================================================
# BALANCE RULES
# =========================================================

st.markdown("### 💰 Balance Rules")

st.info(
    """
    **Financial balance rules**

    Account balances are calculated from the recorded
    financial transactions.

    • Income increases the selected account.  
    • Expenses decrease the selected account.  
    • Transfers move money between accounts without changing
      total balance.  
    • Friend money held is tracked separately as a liability.  
    • Money lent is tracked separately from expenses.  
    • Financial amounts use exact decimal calculations.
    """
)


st.caption(
    "Balance validation is controlled by the transaction "
    "and account services rather than by a page-level toggle."
)


st.divider()


# =========================================================
# SECURITY
# =========================================================

st.markdown("### 🔐 Security")

st.info(
    """
    Your application uses username/password authentication
    with password hashing.

    Supabase credentials are stored through Streamlit Secrets
    and should never be committed to GitHub.
    """
)


st.markdown("#### Current Session")


username = st.session_state.get(
    "username",
    "Unknown user",
)


st.write(
    f"**Logged in as:** {username}"
)


if st.button(
    "🚪 Logout",
    use_container_width=True,
):

    logout()


st.divider()


# =========================================================
# DATA SAFETY
# =========================================================

st.markdown("### 🛡️ Data Safety")

st.info(
    """
    Financial records are stored persistently in Supabase.

    Use the Backup & Restore page to create downloadable
    copies of your supported application data.
    """
)


backup_col1, backup_col2 = st.columns(2)


with backup_col1:

    if st.button(
        "💾 Backup & Restore",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/backup_restore.py"
        )


with backup_col2:

    if st.button(
        "📋 Transaction History",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/Transaction_History.py"
        )


st.divider()


# =========================================================
# ACCOUNT INFORMATION
# =========================================================

st.markdown("### 👤 Account Information")


st.write(
    f"**Username:** {username}"
)


st.write(
    "**Session Status:** Active"
)


st.caption(
    "Account authentication and authorization are managed "
    "through the application's authentication service."
)


st.divider()


# =========================================================
# APPLICATION INFORMATION
# =========================================================

st.markdown("### ℹ️ Application Information")


info_col1, info_col2 = st.columns(2)


with info_col1:

    st.markdown(
        """
        **Expense Tracker**

        - Persistent Supabase storage
        - Decimal-based financial calculations
        - Secure password hashing
        - Transaction history
        - Financial reports
        - Multi-user data isolation
        """
    )


with info_col2:

    st.markdown(
        """
        **Financial Principles**

        - Transfers are not income
        - Transfers are not expenses
        - Friend money is a liability
        - Actual money excludes friend money held
        - Money lent is not an expense
        - Money returned is not income
        - Money calculations use exact decimals
        """
    )


st.divider()


# =========================================================
# IMPORTANT SECURITY NOTE
# =========================================================

st.markdown(
    "### 🔒 Security Reminder"
)


st.warning(
    """
    Never store bank passwords, ATM PINs, UPI PINs,
    CVVs, or complete card numbers in this application.

    Keep downloaded financial backups private and do not
    commit them to GitHub or other public repositories.
    """
)


# =========================================================
# APPLICATION VERSION
# =========================================================

st.caption(
    "Version 1 • Personal Expense Tracker"
)