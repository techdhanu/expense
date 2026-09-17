import streamlit as st
from datetime import date
from decimal import Decimal, InvalidOperation

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)

from services.category_service import get_all_categories

from services.account_service import (
    get_all_accounts,
)

from services.transaction_service import (
    create_income,
    create_expense,
    create_transfer,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Add Transaction",
    "➕",
    "wide",
)

require_login()


# =========================================================
# PAGE HEADER
# =========================================================

show_app_header(
    "Add Transaction",
    "Record your income, expenses, and account transfers.",
)


# =========================================================
# LOAD ACCOUNTS
# =========================================================

try:
    accounts = get_all_accounts()
except Exception as exc:
    st.error(
        f"Unable to load accounts.\n\n{exc}"
    )
    st.stop()


if not accounts:

    st.warning(
        "No active accounts are available. "
        "Create an account before adding a transaction."
    )

    if st.button(
        "🏦 Go to Accounts",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page(
            "pages/accounts.py"
        )

    st.stop()


account_map = {
    account["name"]: account["id"]
    for account in accounts
}


account_names = list(account_map.keys())


# =========================================================
# LOAD CATEGORIES
# =========================================================

try:

    categories = get_all_categories()

except Exception as exc:

    st.error(
        f"Unable to load categories.\n\n{exc}"
    )

    categories = []
# =========================================================
# LOAD PAYMENT METHODS
# =========================================================

PAYMENT_METHODS = {
    "UPI": "upi",
    "Debit Card": "debit_card",
    "Bank Transfer": "bank_transfer",
    "Cash": "cash",
    "Auto Debit": "auto_debit",
    "Other": "other",
}


# =========================================================
# TRANSACTION TYPE
# =========================================================

st.markdown("### 💳 Transaction Type")

transaction_type_label = st.radio(
    "What would you like to record?",
    options=[
        "🟢 Income",
        "🔴 Expense",
        "🔄 Internal Transfer",
    ],
    horizontal=True,
)

if transaction_type_label == "🟢 Income":
    transaction_type = "income"

elif transaction_type_label == "🔴 Expense":
    transaction_type = "expense"

else:
    transaction_type = "internal_transfer"


st.divider()


# =========================================================
# BASIC DETAILS
# =========================================================

st.markdown("### 📅 Transaction Details")

col1, col2 = st.columns(2)

with col1:

    transaction_date = st.date_input(
        "Transaction Date",
        value=date.today(),
        max_value=date.today(),
    )

with col2:

    amount_text = st.text_input(
        "Amount (₹)",
        placeholder="0.00",
        help="Enter the amount using numbers only.",
    )


# =========================================================
# INCOME / EXPENSE
# =========================================================

if transaction_type in (
    "income",
    "expense",
):

    st.markdown("### 🏦 Account")

    selected_account_name = st.selectbox(
        "Account",
        options=account_names,
        help=(
            "Select the account where the money was received "
            if transaction_type == "income"
            else
            "Select the account from which the money was spent."
        ),
    )

    selected_account_id = account_map[
        selected_account_name
    ]


    # -----------------------------------------------------
    # CATEGORY
    # -----------------------------------------------------

    if transaction_type == "income":

        category_options = [
            category
            for category in categories
            if category.get("category_type") == "income"
        ]

        category_label = "Income Category"

    else:

        category_options = [
            category
            for category in categories
            if category.get("category_type") == "expense"
        ]

        category_label = "Expense Category"


    st.markdown("### 🏷️ Classification")


    if category_options:

        category_names = [
            category["name"]
            for category in category_options
        ]

        selected_category_name = st.selectbox(
            category_label,
            options=["No Category"] + category_names,
        )

        if selected_category_name == "No Category":

            selected_category_id = None

        else:

            selected_category_id = next(
                category["id"]
                for category in category_options
                if category["name"]
                == selected_category_name
            )

    else:

        st.info(
            f"No {transaction_type} categories are available yet. "
            "You can continue without a category."
        )

        selected_category_id = None


    # -----------------------------------------------------
    # PAYMENT METHOD
    # -----------------------------------------------------

    selected_payment_method_label = st.selectbox(
        "Payment Method",
        options=[
            "Not Specified",
            *PAYMENT_METHODS.keys(),
        ],
    )

    if selected_payment_method_label == "Not Specified":

        selected_payment_method = None

    else:

        selected_payment_method = PAYMENT_METHODS[
            selected_payment_method_label
        ]


# =========================================================
# INTERNAL TRANSFER
# =========================================================

else:

    st.markdown("### 🔄 Transfer Details")

    col1, col2 = st.columns(2)

    with col1:

        from_account_name = st.selectbox(
            "From Account",
            options=account_names,
            key="transfer_from_account",
        )

    with col2:

        to_account_options = [
            name
            for name in account_names
            if name != from_account_name
        ]

        if not to_account_options:

            st.error(
                "You need at least two different accounts "
                "to create an internal transfer."
            )

            st.stop()

        to_account_name = st.selectbox(
            "To Account",
            options=to_account_options,
            key="transfer_to_account",
        )

    from_account_id = account_map[
        from_account_name
    ]

    to_account_id = account_map[
        to_account_name
    ]


# =========================================================
# DESCRIPTION & NOTES
# =========================================================

st.markdown("### 📝 Additional Information")

description = st.text_input(
    "Description",
    placeholder=(
        "e.g. Monthly salary"
        if transaction_type == "income"
        else
        "e.g. Groceries"
        if transaction_type == "expense"
        else
        "e.g. Transfer to savings"
    ),
    max_chars=200,
)

notes = st.text_area(
    "Notes",
    placeholder="Optional additional details...",
    max_chars=1000,
    height=100,
)


# =========================================================
# REVIEW
# =========================================================

st.divider()

st.markdown("### 🔎 Review")

review_col1, review_col2 = st.columns(2)

with review_col1:

    if transaction_type == "income":

        st.markdown("**Type:** 🟢 Income")

    elif transaction_type == "expense":

        st.markdown("**Type:** 🔴 Expense")

    else:

        st.markdown("**Type:** 🔄 Internal Transfer")


with review_col2:

    if amount_text.strip():

        try:

            preview_amount = Decimal(
                amount_text.strip()
            )

            st.markdown(
                f"**Amount:** ₹{preview_amount:,.2f}"
            )

        except (InvalidOperation, ValueError):

            st.markdown(
                "**Amount:** ⚠️ Invalid"
            )

    else:

        st.markdown(
            "**Amount:** —"
        )


# =========================================================
# SUBMIT
# =========================================================

st.divider()

submit_button = st.button(
    "✅ Save Transaction",
    use_container_width=True,
    type="primary",
)


# =========================================================
# SUBMISSION
# =========================================================

if submit_button:

    # -----------------------------------------------------
    # AMOUNT VALIDATION
    # -----------------------------------------------------

    amount_clean = amount_text.strip()

    if not amount_clean:

        st.error(
            "Please enter an amount."
        )

        st.stop()


    try:

        amount = Decimal(
            amount_clean
        )

    except (InvalidOperation, ValueError):

        st.error(
            "Please enter a valid amount."
        )

        st.stop()


    if amount <= Decimal("0.00"):

        st.error(
            "Amount must be greater than ₹0.00."
        )

        st.stop()


    # -----------------------------------------------------
    # DESCRIPTION CLEANUP
    # -----------------------------------------------------

    description_clean = (
        description.strip()
        if description
        else None
    )

    notes_clean = (
        notes.strip()
        if notes
        else None
    )


    # -----------------------------------------------------
    # CREATE TRANSACTION
    # -----------------------------------------------------

    try:

        # -------------------------------------------------
        # INCOME
        # -------------------------------------------------

        if transaction_type == "income":

            transaction = create_income(
                transaction_date=transaction_date,
                amount=amount,
                account_id=selected_account_id,
                category_id=selected_category_id,
                payment_method=selected_payment_method,
                description=description_clean,
                notes=notes_clean,
            )


            st.success(
                f"Income of ₹{amount:,.2f} "
                f"was recorded successfully."
            )


        # -------------------------------------------------
        # EXPENSE
        # -------------------------------------------------

        elif transaction_type == "expense":

            transaction = create_expense(
                transaction_date=transaction_date,
                amount=amount,
                account_id=selected_account_id,
                category_id=selected_category_id,
                payment_method=selected_payment_method,
                description=description_clean,
                notes=notes_clean,
            )


            st.success(
                f"Expense of ₹{amount:,.2f} "
                f"was recorded successfully."
            )


        # -------------------------------------------------
        # INTERNAL TRANSFER
        # -------------------------------------------------

        else:

            transaction = create_transfer(
                transaction_date=transaction_date,
                amount=amount,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                description=description_clean,
                notes=notes_clean,
            )


            st.success(
                f"₹{amount:,.2f} transferred successfully "
                f"from {from_account_name} "
                f"to {to_account_name}."
            )


        # -------------------------------------------------
        # TRANSACTION ID
        # -------------------------------------------------

        if transaction:

            st.caption(
                f"Transaction ID: `{transaction['id']}`"
            )


        # -------------------------------------------------
        # NEXT ACTIONS
        # -------------------------------------------------

        st.divider()

        next_col1, next_col2 = st.columns(2)

        with next_col1:

            if st.button(
                "➕ Add Another",
                use_container_width=True,
            ):

                st.rerun()


        with next_col2:

            if st.button(
                "📋 View History",
                use_container_width=True,
            ):

                st.switch_page(
                    "pages/Transaction_History.py"
                )


    except Exception as exc:

        st.error(
            f"Transaction could not be saved.\n\n{exc}"
        )