from datetime import date
from decimal import Decimal

import streamlit as st

from utils.constants import PAYMENT_METHODS, TRANSACTION_TYPES
from utils.validators import validate_amount


def transaction_form(
    accounts: list[dict],
    categories: list[dict],
    people: list[dict] | None = None,
    key_prefix: str = "transaction",
) -> dict | None:
    """
    Display the reusable transaction form.

    Returns the submitted form data as a dictionary,
    or None when the form has not been submitted.
    """

    people = people or []

    with st.form(key=f"{key_prefix}_form", clear_on_submit=False):

        st.markdown("### Transaction Details")

        transaction_date = st.date_input(
            "Date",
            value=date.today(),
            key=f"{key_prefix}_date",
        )

        transaction_type = st.selectbox(
            "Transaction Type",
            options=TRANSACTION_TYPES,
            format_func=lambda value: value.replace("_", " ").title(),
            key=f"{key_prefix}_type",
        )

        amount_input = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            step=100.00,
            format="%.2f",
            key=f"{key_prefix}_amount",
        )

        account_options = {
            account["name"]: account["id"]
            for account in accounts
            if account.get("id") and account.get("name")
        }

        category_options = {
            category["name"]: category["id"]
            for category in categories
            if category.get("id") and category.get("name")
        }

        person_options = {
            person["name"]: person["id"]
            for person in people
            if person.get("id") and person.get("name")
        }

        selected_account = None
        destination_account = None
        selected_category = None
        selected_person = None

        if transaction_type == "internal_transfer":

            selected_account = st.selectbox(
                "From Account",
                options=list(account_options.keys()),
                key=f"{key_prefix}_from_account",
            )

            destination_account = st.selectbox(
                "To Account",
                options=list(account_options.keys()),
                key=f"{key_prefix}_to_account",
            )

        else:

            selected_account = st.selectbox(
                "Account",
                options=list(account_options.keys()),
                key=f"{key_prefix}_account",
            )

        if transaction_type in {
            "income",
            "expense",
        }:

            if category_options:
                selected_category = st.selectbox(
                    "Category",
                    options=list(category_options.keys()),
                    key=f"{key_prefix}_category",
                )
            else:
                st.info(
                    "No categories available yet. "
                    "Categories will be added during setup."
                )

        if transaction_type in {
            "friend_money_received",
            "friend_money_returned",
        }:

            if person_options:
                selected_person = st.selectbox(
                    "Person",
                    options=list(person_options.keys()),
                    key=f"{key_prefix}_person",
                )
            else:
                st.info(
                    "No people have been added yet."
                )

        payment_method = st.selectbox(
            "Payment Method",
            options=PAYMENT_METHODS,
            format_func=lambda value: value.replace("_", " ").title(),
            key=f"{key_prefix}_payment_method",
        )

        description = st.text_input(
            "Description",
            placeholder="e.g. Monthly salary, groceries, rent...",
            key=f"{key_prefix}_description",
        )

        notes = st.text_area(
            "Notes (Optional)",
            placeholder="Add any additional details...",
            key=f"{key_prefix}_notes",
        )

        submitted = st.form_submit_button(
            "Save Transaction",
            use_container_width=True,
            type="primary",
        )

    if not submitted:
        return None

    try:
        amount = validate_amount(
            Decimal(str(amount_input))
        )
    except ValueError as exc:
        st.error(str(exc))
        return None

    account_id = (
        account_options[selected_account]
        if selected_account
        else None
    )

    destination_account_id = (
        account_options[destination_account]
        if destination_account
        else None
    )

    category_id = (
        category_options[selected_category]
        if selected_category
        else None
    )

    person_id = (
        person_options[selected_person]
        if selected_person
        else None
    )

    return {
        "transaction_date": transaction_date,
        "transaction_type": transaction_type,
        "amount": amount,
        "source_account_id": account_id,
        "destination_account_id": destination_account_id,
        "category_id": category_id,
        "person_id": person_id,
        "payment_method": payment_method,
        "description": description.strip(),
        "notes": notes.strip(),
    }