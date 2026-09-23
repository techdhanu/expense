import streamlit as st
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from collections import defaultdict

import pandas as pd
import plotly.express as px
import plotly.io as pio

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)

from services.account_service import (
    get_all_account_balances,
)

from services.category_service import (
    get_all_categories,
)

from services.transaction_service import (
    get_filtered_transactions,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Reports",
    "📊",
    "wide",
)

require_login()


# =========================================================
# PAGE HEADER
# =========================================================

show_app_header(
    "Reports & Analytics",
    "Understand where your money comes from and where it goes.",
)


# =========================================================
# REPORTS PAGE STYLING
# =========================================================

# Give every Plotly chart a dark theme that matches the app,
# without touching any of the chart-building code below.
pio.templates.default = "plotly_dark"


# =========================================================
# HELPERS
# =========================================================

def decimal_value(value) -> Decimal:
    """
    Safely convert a value to Decimal.

    Financial calculations always remain Decimal-based.
    """

    if value is None:
        return Decimal("0.00")

    try:

        result = Decimal(
            str(value)
        )

    except (InvalidOperation, ValueError, TypeError):

        return Decimal("0.00")

    if not result.is_finite():

        return Decimal("0.00")

    return result


def format_inr(value) -> str:
    """Format a Decimal-compatible value as INR."""

    return f"₹{decimal_value(value):,.2f}"


# =========================================================
# DATE RANGE
# =========================================================

st.markdown("## 📅 Reporting Period")

today = date.today()


period = st.selectbox(
    "Select Period",
    options=[
        "This Month",
        "Last 30 Days",
        "This Year",
        "All Time",
        "Custom Range",
    ],
    index=0,
)


if period == "This Month":

    start_date = today.replace(
        day=1
    )

    end_date = today


elif period == "Last 30 Days":

    start_date = (
        today
        - timedelta(days=29)
    )

    end_date = today


elif period == "This Year":

    start_date = today.replace(
        month=1,
        day=1,
    )

    end_date = today


elif period == "All Time":

    start_date = date(
        2000,
        1,
        1,
    )

    end_date = today


else:

    custom_col1, custom_col2 = st.columns(2)


    with custom_col1:

        start_date = st.date_input(
            "Start Date",
            value=today.replace(
                day=1
            ),
            max_value=today,
        )


    with custom_col2:

        end_date = st.date_input(
            "End Date",
            value=today,
            max_value=today,
        )


    if start_date > end_date:

        st.error(
            "Start date cannot be after end date."
        )

        st.stop()


st.caption(
    f"Showing financial activity from "
    f"**{start_date.strftime('%d %b %Y')}** "
    f"to **{end_date.strftime('%d %b %Y')}**."
)


# =========================================================
# LOAD TRANSACTIONS
# =========================================================

try:

    transactions = get_filtered_transactions(
        start_date=start_date,
        end_date=end_date,
        transaction_types=None,
        account_ids=None,
        category_ids=None,
        person_ids=None,
    )

except Exception:

    st.error(
        "Unable to load transactions for this report. "
        "Please try again."
    )

    st.stop()


transactions = transactions or []


# =========================================================
# LOAD CATEGORIES
# =========================================================

try:

    categories = get_all_categories()

except Exception:

    st.error(
        "Categories could not be loaded. "
        "Please try again."
    )

    st.stop()


categories = categories or []


category_map = {
    category["id"]: category["name"]
    for category in categories
    if category.get("id")
}


# =========================================================
# LOAD ACCOUNTS
# =========================================================

try:

    account_balances = get_all_account_balances()

except Exception:

    st.error(
        "Account balances could not be loaded. "
        "Please try again."
    )

    st.stop()


account_balances = account_balances or []


# =========================================================
# EMPTY DATASET
# =========================================================

if not transactions:

    st.info(
        "📭 There are no transactions in the selected period."
    )

    st.markdown(
        "Add some transactions to unlock your financial analytics."
    )


    if st.button(
        "➕ Add Transaction",
        use_container_width=True,
        type="primary",
    ):

        st.switch_page(
            "pages/Add_transaction.py"
        )


    st.stop()


# =========================================================
# CORE FINANCIAL CALCULATIONS
# =========================================================

income_total = Decimal("0.00")

expense_total = Decimal("0.00")

transfer_total = Decimal("0.00")

friend_money_received_total = Decimal("0.00")

friend_money_returned_total = Decimal("0.00")

friend_money_lent_total = Decimal("0.00")

friend_money_lent_returned_total = Decimal("0.00")

savings_contribution_total = Decimal("0.00")


for transaction in transactions:

    transaction_type = transaction.get(
        "transaction_type"
    )


    amount = decimal_value(
        transaction.get("amount")
    )


    if transaction_type == "income":

        income_total += amount


    elif transaction_type == "expense":

        expense_total += amount


    elif transaction_type == "internal_transfer":

        transfer_total += amount


    elif transaction_type == "friend_money_received":

        friend_money_received_total += amount


    elif transaction_type == "friend_money_returned":

        friend_money_returned_total += amount


    elif transaction_type == "friend_money_lent":

        friend_money_lent_total += amount


    elif transaction_type == "friend_money_lent_returned":

        friend_money_lent_returned_total += amount


    elif transaction_type == "savings_goal_contribution":

        savings_contribution_total += amount


# ---------------------------------------------------------
# IMPORTANT FINANCIAL RULE
# ---------------------------------------------------------
#
# Net Savings = Income - ordinary Expenses.
#
# Internal transfers, friend-money movements, money lent,
# money-lent returns, and savings-goal contributions are
# intentionally not treated as ordinary income/expense.
# ---------------------------------------------------------

net_savings = (
    income_total
    - expense_total
)


# =========================================================
# SUMMARY CARDS
# =========================================================

st.markdown("## 💰 Financial Summary")


summary1, summary2, summary3, summary4 = st.columns(4)


with summary1:

    st.metric(
        "Income",
        format_inr(income_total),
    )


with summary2:

    st.metric(
        "Expenses",
        format_inr(expense_total),
    )


with summary3:

    st.metric(
        "Net Savings",
        format_inr(net_savings),
    )


with summary4:

    st.metric(
        "Transactions",
        len(transactions),
    )


st.divider()


# =========================================================
# INCOME VS EXPENSE
# =========================================================

st.markdown("### 📊 Income vs Expense")


income_expense_df = pd.DataFrame(
    {
        "Type": [
            "Income",
            "Expense",
        ],
        "Amount": [
            float(income_total),
            float(expense_total),
        ],
    }
)


fig_income_expense = px.bar(
    income_expense_df,
    x="Type",
    y="Amount",
    text="Amount",
    title="Income vs Expense",
)


fig_income_expense.update_traces(
    texttemplate="₹%{text:,.2f}",
    textposition="outside",
)


fig_income_expense.update_layout(
    yaxis_title="Amount (₹)",
    xaxis_title="",
    showlegend=False,
)


st.plotly_chart(
    fig_income_expense,
    use_container_width=True,
)


# =========================================================
# EXPENSE BY CATEGORY
# =========================================================

st.markdown("### 🍩 Expense by Category")


category_totals = defaultdict(
    lambda: Decimal("0.00")
)


for transaction in transactions:

    if transaction.get(
        "transaction_type"
    ) != "expense":

        continue


    category_id = transaction.get(
        "category_id"
    )


    category_name = category_map.get(
        category_id,
        "Uncategorized",
    )


    amount = decimal_value(
        transaction.get("amount")
    )


    category_totals[
        category_name
    ] += amount


if category_totals:

    category_df = pd.DataFrame(
        [
            {
                "Category": category,
                "Amount": float(amount),
            }

            for category, amount
            in category_totals.items()
        ]
    ).sort_values(
        "Amount",
        ascending=False,
    )


    fig_category = px.pie(
        category_df,
        names="Category",
        values="Amount",
        hole=0.55,
        title="Expense Distribution",
    )


    fig_category.update_traces(
        textinfo="label+percent",
        hovertemplate=(
            "%{label}"
            "<br>₹%{value:,.2f}"
            "<br>%{percent}"
            "<extra></extra>"
        ),
    )


    st.plotly_chart(
        fig_category,
        use_container_width=True,
    )

else:

    st.info(
        "No expenses were found in this period."
    )


# =========================================================
# DAILY SPENDING
# =========================================================

st.markdown("### 📈 Daily Spending")


daily_expenses = defaultdict(
    lambda: Decimal("0.00")
)


for transaction in transactions:

    if transaction.get(
        "transaction_type"
    ) != "expense":

        continue


    transaction_date = transaction.get(
        "transaction_date"
    )


    if not transaction_date:

        continue


    amount = decimal_value(
        transaction.get("amount")
    )


    daily_expenses[
        str(transaction_date)[:10]
    ] += amount


if daily_expenses:

    daily_df = pd.DataFrame(
        [
            {
                "Date": transaction_date,
                "Expense": float(amount),
            }

            for transaction_date, amount
            in sorted(
                daily_expenses.items()
            )
        ]
    )


    daily_df["Date"] = pd.to_datetime(
        daily_df["Date"]
    )


    fig_daily = px.line(
        daily_df,
        x="Date",
        y="Expense",
        markers=True,
        title="Daily Spending Trend",
    )


    fig_daily.update_layout(
        yaxis_title="Expense (₹)",
        xaxis_title="Date",
    )


    fig_daily.update_traces(
        hovertemplate=(
            "%{x|%d %b %Y}"
            "<br>₹%{y:,.2f}"
            "<extra></extra>"
        ),
    )


    st.plotly_chart(
        fig_daily,
        use_container_width=True,
    )

else:

    st.info(
        "No expenses found in this period."
    )


# =========================================================
# MONTHLY INCOME VS EXPENSE
# =========================================================

st.markdown("### 📅 Monthly Income vs Expense")


monthly_data = defaultdict(
    lambda: {
        "income": Decimal("0.00"),
        "expense": Decimal("0.00"),
    }
)


for transaction in transactions:

    transaction_type = transaction.get(
        "transaction_type"
    )


    if transaction_type not in (
        "income",
        "expense",
    ):

        continue


    transaction_date = transaction.get(
        "transaction_date"
    )


    if not transaction_date:

        continue


    month_key = str(
        transaction_date
    )[:7]


    amount = decimal_value(
        transaction.get("amount")
    )


    monthly_data[
        month_key
    ][transaction_type] += amount


if monthly_data:

    monthly_rows = []


    for month, values in sorted(
        monthly_data.items()
    ):

        monthly_rows.append(
            {
                "Month": month,
                "Income": float(
                    values["income"]
                ),
                "Expense": float(
                    values["expense"]
                ),
            }
        )


    monthly_df = pd.DataFrame(
        monthly_rows
    )


    monthly_long_df = monthly_df.melt(
        id_vars=["Month"],
        value_vars=[
            "Income",
            "Expense",
        ],
        var_name="Type",
        value_name="Amount",
    )


    fig_monthly = px.bar(
        monthly_long_df,
        x="Month",
        y="Amount",
        color="Type",
        barmode="group",
        title="Monthly Income vs Expense",
    )


    fig_monthly.update_layout(
        yaxis_title="Amount (₹)",
        xaxis_title="Month",
    )


    fig_monthly.update_traces(
        hovertemplate=(
            "%{x}"
            "<br>₹%{y:,.2f}"
            "<extra></extra>"
        ),
    )


    st.plotly_chart(
        fig_monthly,
        use_container_width=True,
    )

else:

    st.info(
        "Not enough data to display monthly analysis."
    )


# =========================================================
# ACCOUNT BALANCES
# =========================================================

st.markdown("### 🏦 Account Balance Distribution")


if account_balances:

    account_rows = []


    for account in account_balances:

        account_name = account.get(
            "account_name",
            account.get(
                "name",
                "Account",
            ),
        )


        balance = decimal_value(
            account.get(
                "current_balance",
                account.get(
                    "balance",
                    "0.00",
                ),
            )
        )


        account_rows.append(
            {
                "Account": account_name,
                "Balance": float(balance),
            }
        )


    if account_rows:

        account_df = pd.DataFrame(
            account_rows
        )


        fig_accounts = px.bar(
            account_df,
            x="Account",
            y="Balance",
            text="Balance",
            title="Current Account Balances",
        )


        fig_accounts.update_traces(
            texttemplate="₹%{text:,.2f}",
            textposition="outside",
        )


        fig_accounts.update_layout(
            yaxis_title="Balance (₹)",
            xaxis_title="",
        )


        st.plotly_chart(
            fig_accounts,
            use_container_width=True,
        )

else:

    st.info(
        "No account balances are available."
    )


# =========================================================
# PAYMENT METHOD BREAKDOWN
# =========================================================

st.markdown("### 💳 Expense by Payment Method")


payment_totals = defaultdict(
    lambda: Decimal("0.00")
)


payment_labels = {
    "upi": "UPI",
    "debit_card": "Debit Card",
    "bank_transfer": "Bank Transfer",
    "cash": "Cash",
    "auto_debit": "Auto Debit",
    "other": "Other",
}


for transaction in transactions:

    if transaction.get(
        "transaction_type"
    ) != "expense":

        continue


    payment_method = transaction.get(
        "payment_method"
    )


    if not payment_method:

        payment_method = "other"


    payment_totals[
        payment_method
    ] += decimal_value(
        transaction.get("amount")
    )


if payment_totals:

    payment_df = pd.DataFrame(
        [
            {
                "Payment Method": payment_labels.get(
                    method,
                    str(method)
                    .replace(
                        "_",
                        " ",
                    )
                    .title(),
                ),
                "Amount": float(amount),
            }

            for method, amount
            in payment_totals.items()
        ]
    )


    fig_payment = px.pie(
        payment_df,
        names="Payment Method",
        values="Amount",
        hole=0.55,
        title="Expense Payment Methods",
    )


    fig_payment.update_traces(
        textinfo="label+percent",
        hovertemplate=(
            "%{label}"
            "<br>₹%{value:,.2f}"
            "<br>%{percent}"
            "<extra></extra>"
        ),
    )


    st.plotly_chart(
        fig_payment,
        use_container_width=True,
    )

else:

    st.info(
        "No expense payment-method data was found "
        "in this period."
    )


# =========================================================
# TRANSACTION ACTIVITY
# =========================================================

st.markdown("### 📋 Activity Summary")


activity_col1, activity_col2, activity_col3 = st.columns(3)


with activity_col1:

    st.metric(
        "Internal Transfers",
        format_inr(transfer_total),
    )


with activity_col2:

    st.metric(
        "Friend Money Received",
        format_inr(
            friend_money_received_total
        ),
    )


with activity_col3:

    st.metric(
        "Friend Money Returned",
        format_inr(
            friend_money_returned_total
        ),
    )


# =========================================================
# ADDITIONAL FINANCIAL MOVEMENTS
# =========================================================

st.markdown("### 🔄 Other Financial Movements")


movement_col1, movement_col2, movement_col3 = st.columns(3)


with movement_col1:

    st.metric(
        "Savings Contributions",
        format_inr(
            savings_contribution_total
        ),
    )


with movement_col2:

    st.metric(
        "Money Lent",
        format_inr(
            friend_money_lent_total
        ),
    )


with movement_col3:

    st.metric(
        "Money Lent Returned",
        format_inr(
            friend_money_lent_returned_total
        ),
    )


st.divider()


# =========================================================
# REPORT NOTES
# =========================================================

st.caption(
    "ℹ️ Internal transfers are shown separately and are not "
    "included in income, expenses, or net savings."
)


st.caption(
    "ℹ️ Friend-money transactions are tracked separately "
    "because they do not represent personal income or spending."
)


st.caption(
    "ℹ️ Savings contributions are tracked separately from "
    "ordinary expenses because they represent money allocated "
    "toward a savings goal."
)


st.caption(
    "🔒 Financial calculations use Decimal values; "
    "floating-point conversion is used only for chart rendering."
)