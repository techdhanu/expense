import streamlit as st

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
    logout,
)

from database.queries import get_table


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
    "Configure how the expense tracker behaves."
)


# ---------------------------------------------------------
# SESSION STATE DEFAULTS
# ---------------------------------------------------------

if "allow_negative_balance" not in st.session_state:

    st.session_state.allow_negative_balance = False


# ---------------------------------------------------------
# BALANCE SETTINGS
# ---------------------------------------------------------

st.markdown("### 💰 Balance Rules")

allow_negative = st.toggle(
    "Allow negative account balances",
    value=st.session_state.allow_negative_balance,
    help=(
        "When enabled, expenses can make an account balance "
        "negative. When disabled, expenses should not exceed "
        "the available account balance."
    ),
)


if allow_negative != st.session_state.allow_negative_balance:

    st.session_state.allow_negative_balance = allow_negative

    st.success(
        "Balance setting updated for this session."
    )


if allow_negative:

    st.warning(
        "⚠️ Negative balances are currently allowed. "
        "Use this only when you intentionally want to "
        "record spending beyond an account's available balance."
    )

else:

    st.info(
        "🛡️ Negative balances are disabled."
    )


st.divider()


# =========================================================
# SECURITY
# =========================================================

st.markdown("### 🔐 Security")

st.info(
    "Your application uses username/password authentication "
    "with password hashing. Supabase secrets remain on the "
    "server and should never be committed to GitHub."
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
    "Financial records are stored persistently in Supabase. "
    "Use the Backup & Restore page to create downloadable "
    "copies of your application data."
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

try:

    response = (
        get_table("app_users")
        .select(
            "username,is_active,created_at"
        )
        .eq(
            "id",
            st.session_state.get("user_id"),
        )
        .limit(1)
        .execute()
    )

    if response.data:

        user = response.data[0]

        st.write(
            f"**Username:** {user.get('username', username)}"
        )

        status = (
            "Active"
            if user.get("is_active", False)
            else "Inactive"
        )

        st.write(
            f"**Account Status:** {status}"
        )

        created_at = user.get(
            "created_at"
        )

        if created_at:

            st.write(
                f"**Account Created:** {created_at}"
            )

except Exception:

    st.caption(
        "Account details could not be loaded."
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
        - Money calculations use exact decimals
        """
    )


st.divider()


# =========================================================
# IMPORTANT NOTE
# =========================================================

st.caption(
    "🔒 Never store bank passwords, ATM PINs, UPI PINs, "
    "CVVs, or complete card numbers in this application."
)

st.caption(
    "Version 1 • Personal Expense Tracker"
)