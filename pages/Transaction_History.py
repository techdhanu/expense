import streamlit as st
from datetime import date as date_type
from decimal import Decimal

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)
from components.filters import (
    transaction_filters,
    clear_filters_button,
)
from services.transaction_service import get_filtered_transactions
from services.account_service import get_all_accounts
from services.friend_money_service import get_all_people
from database.queries import get_categories
from services.export_service import (
    build_transaction_dataframe,
    export_transactions_csv,
    export_transactions_excel,
    export_transactions_pdf,
)


# =========================================================
# PAGE SETUP
# =========================================================

setup_page(
    "Transaction History",
    "View your complete financial transaction history",
)

require_login()

show_app_header(
    "Transaction History",
    "View and review your financial activity",
)


# =========================================================
# LOAD SUPPORTING DATA
# =========================================================

accounts = get_all_accounts()
categories = get_categories()
people = get_all_people()


# =========================================================
# PAGE TITLE
# =========================================================

st.markdown("## 📋 Transaction History")


# =========================================================
# FILTERS
# =========================================================

st.markdown("### 🔎 Filters")

filters = transaction_filters(
    accounts=accounts,
    categories=categories,
    key_prefix="history",
)


# =========================================================
# CLEAR FILTERS
# =========================================================

if clear_filters_button("clear_history_filters"):

    filter_keys = [
        "history_date_start",
        "history_date_end",
        "history_types",
        "history_accounts",
        "history_categories",
    ]

    for key in filter_keys:
        st.session_state.pop(key, None)

    st.rerun()


# =========================================================
# LOAD FILTERED TRANSACTIONS
# =========================================================

with st.spinner("Loading transactions..."):

    transactions = get_filtered_transactions(
        start_date=filters["start_date"],
        end_date=filters["end_date"],
        transaction_types=filters["transaction_types"] or None,
        account_ids=filters["account_ids"] or None,
        category_ids=filters["category_ids"] or None,
    )


# =========================================================
# EMPTY RESULT HANDLING
# =========================================================

if not transactions:

    st.info(
        "No transactions found for the selected filters."
    )

    st.stop()


# =========================================================
# CREATE LOOKUP MAPS
# =========================================================

account_map = {
    account["id"]: account["name"]
    for account in accounts
    if account.get("id") and account.get("name")
}

category_map = {
    category["id"]: category["name"]
    for category in categories
    if category.get("id") and category.get("name")
}

person_map = {
    person["id"]: person["name"]
    for person in people
    if person.get("id") and person.get("name")
}


# =========================================================
# BUILD DISPLAY / EXPORT DATAFRAME
# =========================================================

df = build_transaction_dataframe(
    transactions=transactions,
    account_map=account_map,
    category_map=category_map,
    person_map=person_map,
)


# =========================================================
# SUMMARY CALCULATIONS
# =========================================================

income_total = Decimal("0.00")
expense_total = Decimal("0.00")

for transaction in transactions:

    amount = Decimal(
        str(transaction.get("amount", "0"))
    )

    transaction_type = transaction.get(
        "transaction_type"
    )

    if transaction_type == "income":
        income_total += amount

    elif transaction_type == "expense":
        expense_total += amount


# =========================================================
# SUMMARY CARDS
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Transactions",
        len(transactions),
    )

with col2:
    st.metric(
        "Income",
        f"₹{income_total:,.2f}",
    )

with col3:
    st.metric(
        "Expenses",
        f"₹{expense_total:,.2f}",
    )


st.divider()


# =========================================================
# TRANSACTION TABLE
# =========================================================

st.markdown(
    f"### Transactions ({len(transactions)})"
)

# Create a separate dataframe for visual formatting.
# The original dataframe remains untouched for exports.
display_df = df.copy()

if "Amount" in display_df.columns:

    display_df["Amount"] = display_df[
        "Amount"
    ].apply(
        lambda value: f"₹{Decimal(str(value)):,.2f}"
    )

for _column_name in ("Debit", "Credit"):

    if _column_name in display_df.columns:

        display_df[_column_name] = display_df[
            _column_name
        ].apply(
            lambda value: (
                f"₹{Decimal(str(value)):,.2f}"
                if value is not None
                else ""
            )
        )

if "Date" in display_df.columns:

    def _format_display_date(value):
        """Format a stored date as a human-friendly date for display only."""
        if not value:
            return value
        try:
            return date_type.fromisoformat(
                str(value)[:10]
            ).strftime("%d %b %Y")
        except (ValueError, TypeError):
            return value

    display_df["Date"] = display_df[
        "Date"
    ].apply(_format_display_date)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# EXPORT SECTION
# =========================================================

st.divider()

st.markdown("### 📥 Export Transactions")

st.caption(
    "Exports contain only the transactions currently "
    "matching your selected filters."
)


# =========================================================
# GENERATE EXPORT FILES
# =========================================================

csv_data = export_transactions_csv(df)

excel_data = export_transactions_excel(df)

pdf_data = export_transactions_pdf(
    df,
    title="Transaction History",
)


# =========================================================
# DOWNLOAD BUTTONS
# =========================================================

export_col1, export_col2, export_col3 = st.columns(3)


with export_col1:

    st.download_button(
        label="📄 Download CSV",
        data=csv_data,
        file_name="transaction_history.csv",
        mime="text/csv",
        use_container_width=True,
    )


with export_col2:

    st.download_button(
        label="📊 Download Excel",
        data=excel_data,
        file_name="transaction_history.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )


with export_col3:

    st.download_button(
        label="🧾 Download PDF",
        data=pdf_data,
        file_name="transaction_history.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# =========================================================
# IMMUTABILITY NOTICE
# =========================================================

st.divider()

st.caption(
    "🔒 Transaction records are immutable from this page. "
    "No edit or delete operations are available."
)