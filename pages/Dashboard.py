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
    get_total_money_lent_outstanding,
)
from services.transaction_service import (
    get_filtered_transactions,
)
from services.savings_service import (
    get_all_savings_goals,
    get_goal_status,
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

with st.spinner("Loading your financial overview..."):

    account_balances = get_all_account_balances()

    total_balance = get_total_current_balance()

    friend_money_held = get_total_friend_money_held()

    actual_money = calculate_actual_money(
        total_balance,
        friend_money_held,
    )

    # Money lent out to others, still outstanding.
    try:
        money_lent_outstanding = Decimal(
            str(get_total_money_lent_outstanding() or "0.00")
        )
    except Exception:
        money_lent_outstanding = Decimal("0.00")

    # Total contributed so far across active savings goals.
    try:
        total_savings = Decimal("0.00")

        for goal in get_all_savings_goals():
            if goal.get("status") == "active":
                goal_status = get_goal_status(goal["id"])
                total_savings += Decimal(
                    str(goal_status.get("contributed", "0.00"))
                )
    except Exception:
        total_savings = Decimal("0.00")

    # -------------------------------------------------------
    # MONTH-TO-DATE TRENDS
    #
    # Computed directly from this month's recorded transactions
    # so the KPI deltas are always genuinely correct instead of
    # a fabricated/estimated percentage.
    #
    # Internal transfers are intentionally excluded: they move
    # money between the user's own accounts and therefore never
    # change the combined total balance.
    # -------------------------------------------------------
    try:
        month_start_date = date.today().replace(day=1)

        month_transactions = get_filtered_transactions(
            start_date=month_start_date,
            end_date=date.today(),
            transaction_types=None,
            account_ids=None,
            category_ids=None,
        )

        total_balance_change = Decimal("0.00")
        friend_money_change = Decimal("0.00")

        for month_transaction in month_transactions:

            month_transaction_type = month_transaction.get(
                "transaction_type"
            )

            month_transaction_amount = Decimal(
                str(month_transaction.get("amount", "0.00"))
            )

            if month_transaction_type == "income":
                total_balance_change += month_transaction_amount

            elif month_transaction_type == "expense":
                total_balance_change -= month_transaction_amount

            elif month_transaction_type == "friend_money_received":
                total_balance_change += month_transaction_amount
                friend_money_change += month_transaction_amount

            elif month_transaction_type == "friend_money_returned":
                total_balance_change -= month_transaction_amount
                friend_money_change -= month_transaction_amount

            elif month_transaction_type == "friend_money_lent":
                total_balance_change -= month_transaction_amount

            elif month_transaction_type == "friend_money_lent_returned":
                total_balance_change += month_transaction_amount

            elif month_transaction_type == "balance_adjustment":
                total_balance_change += month_transaction_amount

            elif month_transaction_type == "savings_goal_contribution":
                total_balance_change -= month_transaction_amount

            # internal_transfer intentionally excluded above.

        actual_money_change = (
            total_balance_change
            - friend_money_change
        )

    except Exception:
        total_balance_change = None
        friend_money_change = None
        actual_money_change = None


def _format_month_delta(change: Decimal | None) -> str | None:
    """
    Format a month-to-date change as a signed INR delta string
    for use with st.metric, or None when it cannot be calculated.
    """

    if change is None:
        return None

    sign = "+" if change >= Decimal("0.00") else "-"

    return f"{sign}₹{abs(change):,.2f} this month"


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

account_count = len(account_balances)

with col1:
    st.metric(
        "Total Balance",
        f"₹{Decimal(str(total_balance)):,.2f}",
        delta=_format_month_delta(total_balance_change),
    )
    st.caption(
        f"Across {account_count} "
        f"account{'s' if account_count != 1 else ''}"
    )

with col2:
    st.metric(
        "Actual Money",
        f"₹{Decimal(str(actual_money)):,.2f}",
        delta=_format_month_delta(actual_money_change),
    )
    st.caption("Your own available money")

with col3:
    st.metric(
        "Friend's Money Held",
        f"₹{Decimal(str(friend_money_held)):,.2f}",
        delta=_format_month_delta(friend_money_change),
        delta_color="inverse",
        help=(
            "this is money you owe back to others, so an "
            "increase is shown in red (it's a liability) and"
            " a decrease is shown in green (you owe less)"
        )
    )
    st.caption("Money belonging to others")


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

action4, action5 = st.columns(2)

with action4:

    if st.button(
        "👥 Friends' Money",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/friends_money.py"
        )

with action5:

    if st.button(
        "🎯 Savings Goals",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/savings_goal.py"
        )


st.divider()


# =========================================================
# ACCOUNT BALANCES
# =========================================================

balances_header, balances_link = st.columns([0.75, 0.25])

with balances_header:

    st.markdown("### 🏦 Account Balances")

with balances_link:

    st.page_link(
        "pages/accounts.py",
        label="View accounts →",
    )

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

        account_type = account.get(
            "account_type",
            "Bank Account",
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

            st.caption(
                str(account_type).replace(
                    "_", " "
                ).title()
            )

            st.metric(
                label="Available Balance",
                value=f"₹{balance:,.2f}",
            )


st.divider()


# =========================================================
# MONEY SNAPSHOT
# =========================================================

st.markdown("### 📊 Money Snapshot")

st.caption(
    "How your total balance breaks down across what's "
    "yours, what's held for others, and what's saved."
)

snapshot_rows = [
    ("Your money", actual_money),
    ("Money held for others", friend_money_held),
    ("Money lent out", money_lent_outstanding),
    ("Savings", total_savings),
]

for label, value in snapshot_rows:

    snapshot_label_col, snapshot_value_col = st.columns(
        [0.7, 0.3]
    )

    with snapshot_label_col:

        st.markdown(label)

    with snapshot_value_col:

        st.markdown(
            f"**₹{Decimal(str(value)):,.2f}**"
        )


st.divider()


# =========================================================
# RECENT TRANSACTIONS
# =========================================================

transactions_header, transactions_link = st.columns(
    [0.75, 0.25]
)

with transactions_header:

    st.markdown("### 🧾 Recent Transactions")

with transactions_link:

    st.page_link(
        "pages/Transaction_History.py",
        label="View all →",
    )

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
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🔒 Financial balances are calculated from your recorded "
    "transactions and account opening balances."
)