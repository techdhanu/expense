from datetime import date, timedelta

import streamlit as st


def date_range_filter(
    key_prefix: str = "date_filter",
) -> tuple[date, date]:
    """
    Display a date-range filter and return the selected dates.
    """

    today = date.today()

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "From",
            value=today - timedelta(days=30),
            key=f"{key_prefix}_start",
        )

    with col2:
        end_date = st.date_input(
            "To",
            value=today,
            key=f"{key_prefix}_end",
        )

    if start_date > end_date:
        st.error("Start date cannot be after end date.")
        return end_date, start_date

    return start_date, end_date


def transaction_filters(
    accounts: list[dict] | None = None,
    categories: list[dict] | None = None,
    key_prefix: str = "transaction_filter",
) -> dict:
    """
    Display common transaction filters.
    """

    accounts = accounts or []
    categories = categories or []

    start_date, end_date = date_range_filter(
        key_prefix=f"{key_prefix}_date"
    )

    col1, col2 = st.columns(2)

    with col1:
        transaction_types = st.multiselect(
            "Transaction Type",
            options=[
                "income",
                "expense",
                "internal_transfer",
                "friend_money_received",
                "friend_money_returned",
                "balance_adjustment",
                "savings_goal_contribution",
            ],
            key=f"{key_prefix}_types",
        )

    with col2:
        account_options = {
            account["name"]: account["id"]
            for account in accounts
            if account.get("id") and account.get("name")
        }

        selected_accounts = st.multiselect(
            "Account",
            options=list(account_options.keys()),
            key=f"{key_prefix}_accounts",
        )

    category_options = {
        category["name"]: category["id"]
        for category in categories
        if category.get("id") and category.get("name")
    }

    selected_categories = st.multiselect(
        "Category",
        options=list(category_options.keys()),
        key=f"{key_prefix}_categories",
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "transaction_types": transaction_types,
        "account_ids": [
            account_options[name]
            for name in selected_accounts
        ],
        "category_ids": [
            category_options[name]
            for name in selected_categories
        ],
    }


def clear_filters_button(
    key: str = "clear_filters",
) -> bool:
    """
    Display a clear-filters button.
    """

    return st.button(
        "Clear Filters",
        key=key,
        use_container_width=True,
    )