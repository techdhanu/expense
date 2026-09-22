import streamlit as st
from datetime import date
from decimal import Decimal

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)
from services.account_service import (
    get_all_account_balances,
    get_total_current_balance,
)
from services.friend_money_service import (
    get_total_friend_money_held,
)
from services.transaction_service import (
    get_filtered_transactions,
)
from utils.calculations import calculate_actual_money


# =========================================================
# PAGE SETUP
# =========================================================

setup_page(
    title="Dashboard",
    icon="🏠",
    layout="wide",
)

require_login()

show_app_header(
    "Dashboard",
    "Your financial overview at a glance",
)


# =========================================================
# LOAD FINANCIAL DATA
# =========================================================

account_balances = get_all_account_balances()

total_balance = get_total_current_balance()

friend_money_held = get_total_friend_money_held()

actual_money = calculate_actual_money(
    total_balance,
    friend_money_held,
)


# =========================================================
# FINANCIAL OVERVIEW
# =========================================================

st.markdown("## 💰 Financial Overview")

st.caption(
    "A clear view of your available money, account balances, "
    "and money currently held for others."
)


# =========================================================
# MAIN KPI CARDS
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Balance",
        f"₹{Decimal(str(total_balance)):,.2f}",
    )

with col2:
    st.metric(
        "Actual Money",
        f"₹{Decimal(str(actual_money)):,.2f}",
    )

with col3:
    st.metric(
        "Friend's Money Held",
        f"₹{Decimal(str(friend_money_held)):,.2f}",
    )


st.divider()


# =========================================================
# ACCOUNT BALANCES
# =========================================================

st.markdown("### 🏦 Account Balances")

if not account_balances:

    st.info("No active accounts found.")

else:

    account_columns = st.columns(
        min(len(account_balances), 3)
    )

    for index, account in enumerate(account_balances):

        account_name = account.get(
            "account_name",
            account.get(
                "name",
                "Account",
            ),
        )

        balance = Decimal(
            str(
                account.get(
                    "current_balance",
                    account.get(
                        "balance",
                        "0.00",
                    ),
                )
            )
        )

        with account_columns[
            index % len(account_columns)
        ]:

            st.markdown(
                f"**🏦 {account_name}**"
            )

            st.metric(
                label="Current Balance",
                value=f"₹{balance:,.2f}",
            )


st.divider()


# =========================================================
# RECENT TRANSACTIONS
# =========================================================

st.markdown("### 🧾 Recent Transactions")

recent_transactions = get_filtered_transactions(
    start_date=date.min,
    end_date=date.max,
    transaction_types=None,
    account_ids=None,
    category_ids=None,
)


# Keep only the latest five transactions.
recent_transactions = recent_transactions[:5]


if not recent_transactions:

    st.info(
        "No transactions yet. "
        "Add your first transaction to see activity here."
    )

else:

    for transaction in recent_transactions:

        transaction_type = transaction.get(
            "transaction_type",
            "",
        )

        amount = Decimal(
            str(
                transaction.get(
                    "amount",
                    "0.00",
                )
            )
        )

        description = (
            transaction.get("description")
            or transaction_type.replace(
                "_",
                " ",
            ).title()
        )

        transaction_date = transaction.get(
            "transaction_date",
            "",
        )


        # -------------------------------------------------
        # TRANSACTION DISPLAY METADATA
        # -------------------------------------------------

        if transaction_type == "income":

            icon = "🟢"
            prefix = "+"

        elif transaction_type == "expense":

            icon = "🔴"
            prefix = "-"

        elif transaction_type == "internal_transfer":

            icon = "🔄"
            prefix = ""

        elif transaction_type == "friend_money_received":

            icon = "👥"
            prefix = "+"

        elif transaction_type == "friend_money_returned":

            icon = "↩️"
            prefix = "-"

        elif transaction_type == "savings_goal_contribution":

            icon = "🎯"
            prefix = "-"

        elif transaction_type == "friend_money_lent":

            icon = "💸"
            prefix = "-"

        elif transaction_type == "friend_money_lent_returned":

            icon = "↩️"
            prefix = "+"

        else:

            icon = "💳"
            prefix = ""


        # -------------------------------------------------
        # TRANSACTION ROW
        # -------------------------------------------------

        col1, col2, col3 = st.columns(
            [0.10, 0.60, 0.30]
        )

        with col1:

            st.markdown(
                f"### {icon}"
            )

        with col2:

            st.markdown(
                f"**{description}**"
            )

            st.caption(
                f"{transaction_date} • "
                f"{transaction_type.replace('_', ' ').title()}"
            )

        with col3:

            st.markdown(
                f"**{prefix}₹{amount:,.2f}**"
            )

        st.divider()


# =========================================================
# QUICK ACTIONS
# =========================================================

st.markdown("### ⚡ Quick Actions")

action1, action2, action3 = st.columns(3)


with action1:

    if st.button(
        "➕ Add Transaction",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/Add_transaction.py"
        )


with action2:

    if st.button(
        "📋 Transaction History",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/Transaction_History.py"
        )


with action3:

    if st.button(
        "🏦 Accounts",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/accounts.py"
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🔒 Financial balances are calculated from your recorded "
    "transactions and account opening balances."
)