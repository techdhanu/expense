import streamlit as st
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)

from services.recurring_service import (
    get_all_recurring_transactions,
    create_recurring_transaction,
    update_recurring_transaction,
    deactivate_recurring_transaction,
    activate_recurring_transaction,
    get_due_recurring_transactions,
)

from services.account_service import (
    get_all_accounts,
)

from services.category_service import (
    get_all_categories,
)

from utils.constants import (
    RECURRING_FREQUENCIES,
    PAYMENT_METHODS,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Recurring Transactions",
    "🔄",
    "wide",
)

require_login()

show_app_header(
    "Recurring Transactions",
    "Manage your regular income, expenses, and transfers.",
)


# =========================================================
# HELPERS
# =========================================================

def money(value) -> Decimal:
    """Safely convert a value to Decimal."""
    return Decimal(str(value or "0.00"))


def format_inr(value) -> str:
    """Format amount as INR."""
    return f"₹{money(value):,.2f}"


def parse_date(value):
    """Safely convert database date values."""
    if not value:
        return None

    try:
        return date.fromisoformat(
            str(value)[:10]
        )
    except ValueError:
        return None


# =========================================================
# LOAD SUPPORTING DATA
# =========================================================

try:

    accounts = get_all_accounts()
    categories = get_all_categories()

except Exception as exc:

    st.error(
        "Required account/category data could not be loaded."
    )

    st.caption(str(exc))

    st.stop()


account_map = {
    account["id"]: account["name"]
    for account in accounts
}


category_map = {
    category["id"]: category["name"]
    for category in categories
}


# =========================================================
# DUE TRANSACTIONS ALERT
# =========================================================

try:

    due_transactions = (
        get_due_recurring_transactions(
            date.today()
        )
    )

except Exception:

    due_transactions = []


if due_transactions:

    st.warning(
        f"🔔 **{len(due_transactions)} recurring "
        "transaction(s) are due.**"
    )

    st.caption(
        "Review the due items below and process them "
        "through your transaction workflow when appropriate."
    )


# =========================================================
# CREATE RECURRING TRANSACTION
# =========================================================

st.markdown("## ➕ Create Recurring Transaction")

st.caption(
    "Set up a regular income, expense, or account transfer."
)


with st.form(
    "create_recurring_transaction_form",
    clear_on_submit=True,
):

    transaction_name = st.text_input(
        "Transaction Name",
        placeholder="Example: Netflix Subscription",
    )

    col1, col2 = st.columns(2)

    with col1:

        transaction_type = st.selectbox(
            "Transaction Type",
            options=[
                "expense",
                "income",
                "internal_transfer",
            ],
            format_func=lambda value: {
                "expense": "💸 Expense",
                "income": "💰 Income",
                "internal_transfer": "🔄 Internal Transfer",
            }[value],
        )

    with col2:

        frequency = st.selectbox(
            "Frequency",
            options=RECURRING_FREQUENCIES,
            format_func=lambda value: value.capitalize(),
        )


    amount_text = st.text_input(
        "Amount",
        placeholder="Example: 999",
    )


    account_options = [
        account["id"]
        for account in accounts
    ]


    if account_options:

        account_id = st.selectbox(
            "Account",
            options=account_options,
            format_func=lambda value:
                account_map[value],
        )

    else:

        account_id = None

        st.warning(
            "Create an account before adding recurring transactions."
        )


    destination_account_id = None


    if transaction_type == "internal_transfer":

        destination_options = [
            account["id"]
            for account in accounts
            if account["id"] != account_id
        ]

        if destination_options:

            destination_account_id = st.selectbox(
                "Destination Account",
                options=destination_options,
                format_func=lambda value:
                    account_map[value],
            )

        else:

            st.warning(
                "At least two different accounts are required "
                "for an internal transfer."
            )


    category_id = None


    if transaction_type in {
        "expense",
        "income",
    }:

        category_options = [
            category["id"]
            for category in categories
        ]

        if category_options:

            category_id = st.selectbox(
                "Category",
                options=[None] + category_options,
                format_func=lambda value:
                    "No Category"
                    if value is None
                    else category_map[value],
            )

        else:

            st.info(
                "No categories are currently available."
            )


    payment_method = None


    if transaction_type != "internal_transfer":

        payment_method = st.selectbox(
            "Payment Method",
            options=[None] + PAYMENT_METHODS,
            format_func=lambda value:
                "Not specified"
                if value is None
                else value.replace("_", " ").title(),
        )


    col3, col4 = st.columns(2)

    with col3:

        start_date = st.date_input(
            "Start Date",
            value=date.today(),
        )

    with col4:

        next_due_date = st.date_input(
            "Next Due Date",
            value=date.today(),
        )


    auto_create = st.checkbox(
        "Automatically create transactions when due",
        value=False,
        help=(
            "The current service stores this preference. "
            "Automatic transaction execution will be handled "
            "by the recurring-processing workflow."
        ),
    )


    notes = st.text_area(
        "Notes",
        placeholder="Optional notes...",
        height=90,
    )


    create_button = st.form_submit_button(
        "🔄 Create Recurring Transaction",
        use_container_width=True,
        type="primary",
    )


if create_button:

    if not transaction_name.strip():

        st.error(
            "Please enter a transaction name."
        )

    elif not amount_text.strip():

        st.error(
            "Please enter an amount."
        )

    elif account_id is None:

        st.error(
            "Please select an account."
        )

    elif (
        transaction_type == "internal_transfer"
        and destination_account_id is None
    ):

        st.error(
            "Please select a destination account."
        )

    elif next_due_date < start_date:

        st.error(
            "Next due date cannot be before the start date."
        )

    else:

        try:

            amount = Decimal(
                amount_text.strip()
            )

            if amount <= Decimal("0.00"):

                st.error(
                    "Amount must be greater than ₹0."
                )

            else:

                try:

                    create_recurring_transaction(
                        transaction_name=transaction_name,
                        transaction_type=transaction_type,
                        amount=amount,
                        account_id=account_id,
                        frequency=frequency,
                        start_date=start_date,
                        next_due_date=next_due_date,
                        destination_account_id=destination_account_id,
                        category_id=category_id,
                        payment_method=payment_method,
                        auto_create=auto_create,
                        notes=notes,
                    )

                    st.success(
                        "Recurring transaction created successfully."
                    )

                    st.rerun()

                except ValueError as exc:

                    st.error(
                        str(exc)
                    )

                except Exception:

                    st.error(
                        "Recurring transaction could not be created."
                    )

        except InvalidOperation:

            st.error(
                "Please enter a valid numeric amount."
            )


st.divider()


# =========================================================
# LOAD ALL RECURRING TRANSACTIONS
# =========================================================

try:

    recurring_transactions = (
        get_all_recurring_transactions(
            active_only=False
        )
    )

except Exception as exc:

    st.error(
        "Recurring transactions could not be loaded."
    )

    st.caption(str(exc))

    st.stop()


# =========================================================
# EMPTY STATE
# =========================================================

if not recurring_transactions:

    st.info(
        "No recurring transactions have been configured yet."
    )

    st.markdown(
        """
        **Examples:**

        • Monthly subscriptions  
        • Monthly salary  
        • Rent or regular bills  
        • Weekly allowances  
        • Regular transfers between your accounts
        """
    )

    st.stop()


# =========================================================
# SUMMARY
# =========================================================

active_items = [
    item
    for item in recurring_transactions
    if item.get("is_active") is True
]

inactive_items = [
    item
    for item in recurring_transactions
    if item.get("is_active") is not True
]

due_count = len(due_transactions)


summary1, summary2, summary3 = st.columns(3)

with summary1:

    st.metric(
        "Active",
        len(active_items),
    )

with summary2:

    st.metric(
        "Due",
        due_count,
    )

with summary3:

    st.metric(
        "Inactive",
        len(inactive_items),
    )


st.divider()


# =========================================================
# ACTIVE TRANSACTIONS
# =========================================================

st.markdown("## 🔄 Active Recurring Transactions")


if not active_items:

    st.info(
        "There are no active recurring transactions."
    )

else:

    for item in active_items:

        recurring_id = item["id"]

        transaction_name = item.get(
            "transaction_name",
            "Unnamed",
        )

        transaction_type = item.get(
            "transaction_type",
            "",
        )

        amount = money(
            item.get("amount")
        )

        frequency = item.get(
            "frequency",
            "",
        )

        account_id = item.get(
            "account_id"
        )

        destination_id = item.get(
            "destination_account_id"
        )

        category_id = item.get(
            "category_id"
        )

        payment_method = item.get(
            "payment_method"
        )

        next_due = parse_date(
            item.get("next_due_date")
        )

        start_date_value = parse_date(
            item.get("start_date")
        )

        auto_create_value = item.get(
            "auto_create",
            False,
        )


        # -------------------------------------------------
        # DUE STATUS
        # -------------------------------------------------

        if next_due:

            if next_due < date.today():

                due_label = (
                    "🔴 Overdue"
                )

            elif next_due == date.today():

                due_label = (
                    "🟠 Due today"
                )

            else:

                days_until = (
                    next_due - date.today()
                ).days

                if days_until <= 7:

                    due_label = (
                        f"🟡 Due in {days_until} day(s)"
                    )

                else:

                    due_label = (
                        "🟢 Scheduled"
                    )

        else:

            due_label = "⚪ No due date"


        # -------------------------------------------------
        # TYPE ICON
        # -------------------------------------------------

        type_icon = {
            "income": "💰",
            "expense": "💸",
            "internal_transfer": "🔄",
        }.get(
            transaction_type,
            "🔁",
        )


        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        st.markdown(
            f"### {type_icon} {transaction_name}"
        )

        st.caption(
            f"{due_label} • "
            f"{frequency.capitalize()} • "
            f"{format_inr(amount)}"
        )


        # -------------------------------------------------
        # DETAILS
        # -------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown("**Account**")

            st.write(
                account_map.get(
                    account_id,
                    "Unknown Account",
                )
            )

        with col2:

            st.markdown("**Next Due**")

            if next_due:

                st.write(
                    next_due.strftime(
                        "%d %b %Y"
                    )
                )

            else:

                st.write("Not set")

        with col3:

            st.markdown("**Auto Create**")

            st.write(
                "Enabled"
                if auto_create_value
                else "Manual"
            )


        if transaction_type == "internal_transfer":

            transfer_col1, transfer_col2 = st.columns(2)

            with transfer_col1:

                st.markdown(
                    "**From Account**"
                )

                st.write(
                    account_map.get(
                        account_id,
                        "Unknown Account",
                    )
                )

            with transfer_col2:

                st.markdown(
                    "**To Account**"
                )

                st.write(
                    account_map.get(
                        destination_id,
                        "Unknown Account",
                    )
                )

        else:

            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:

                if category_id:

                    st.markdown(
                        "**Category**"
                    )

                    st.write(
                        category_map.get(
                            category_id,
                            "Unknown Category",
                        )
                    )

            with detail_col2:

                if payment_method:

                    st.markdown(
                        "**Payment Method**"
                    )

                    st.write(
                        payment_method
                        .replace("_", " ")
                        .title()
                    )


        # -------------------------------------------------
        # EDIT
        # -------------------------------------------------

        with st.expander(
            "✏️ Edit"
        ):

            edit_name = st.text_input(
                "Transaction Name",
                value=transaction_name,
                key=f"edit_name_{recurring_id}",
            )

            edit_amount_text = st.text_input(
                "Amount",
                value=f"{amount:.2f}",
                key=f"edit_amount_{recurring_id}",
            )

            edit_frequency = st.selectbox(
                "Frequency",
                options=RECURRING_FREQUENCIES,
                index=(
                    RECURRING_FREQUENCIES.index(
                        frequency
                    )
                    if frequency in RECURRING_FREQUENCIES
                    else 0
                ),
                format_func=lambda value:
                    value.capitalize(),
                key=f"edit_frequency_{recurring_id}",
            )


            edit_next_due = st.date_input(
                "Next Due Date",
                value=next_due or date.today(),
                key=f"edit_next_due_{recurring_id}",
            )


            edit_start_date = st.date_input(
                "Start Date",
                value=start_date_value or date.today(),
                key=f"edit_start_date_{recurring_id}",
            )


            edit_auto_create = st.checkbox(
                "Automatically create when due",
                value=bool(auto_create_value),
                key=f"edit_auto_create_{recurring_id}",
            )


            edit_notes = st.text_area(
                "Notes",
                value=item.get("notes") or "",
                key=f"edit_notes_{recurring_id}",
            )


            if st.button(
                "💾 Save Changes",
                key=f"save_{recurring_id}",
                use_container_width=True,
            ):

                if not edit_name.strip():

                    st.error(
                        "Transaction name cannot be empty."
                    )

                elif not edit_amount_text.strip():

                    st.error(
                        "Amount is required."
                    )

                elif edit_next_due < edit_start_date:

                    st.error(
                        "Next due date cannot be before "
                        "the start date."
                    )

                else:

                    try:

                        edit_amount = Decimal(
                            edit_amount_text.strip()
                        )

                        if edit_amount <= Decimal("0.00"):

                            st.error(
                                "Amount must be greater than ₹0."
                            )

                        else:

                            update_recurring_transaction(
                                recurring_id,
                                {
                                    "transaction_name": edit_name,
                                    "amount": edit_amount,
                                    "frequency": edit_frequency,
                                    "start_date": edit_start_date,
                                    "next_due_date": edit_next_due,
                                    "auto_create": edit_auto_create,
                                    "notes": edit_notes,
                                },
                            )

                            st.success(
                                "Recurring transaction updated."
                            )

                            st.rerun()

                    except InvalidOperation:

                        st.error(
                            "Please enter a valid amount."
                        )

                    except ValueError as exc:

                        st.error(
                            str(exc)
                        )

                    except Exception:

                        st.error(
                            "Recurring transaction could not be updated."
                        )


        # -------------------------------------------------
        # DEACTIVATE
        # -------------------------------------------------

        with st.expander(
            "⚙️ Management"
        ):

            st.warning(
                "Deactivating a recurring transaction keeps "
                "its configuration and history but prevents "
                "it from being treated as active."
            )


            if st.button(
                "⏸️ Deactivate",
                key=f"deactivate_{recurring_id}",
                use_container_width=True,
            ):

                try:

                    deactivate_recurring_transaction(
                        recurring_id
                    )

                    st.success(
                        "Recurring transaction deactivated."
                    )

                    st.rerun()

                except Exception:

                    st.error(
                        "Recurring transaction could not be deactivated."
                    )


        st.divider()


# =========================================================
# INACTIVE TRANSACTIONS
# =========================================================

if inactive_items:

    with st.expander(
        f"⏸️ Inactive Transactions ({len(inactive_items)})"
    ):

        for item in inactive_items:

            recurring_id = item["id"]

            transaction_name = item.get(
                "transaction_name",
                "Unnamed",
            )

            amount = money(
                item.get("amount")
            )

            frequency = item.get(
                "frequency",
                "",
            )


            st.markdown(
                f"**{transaction_name}**"
            )

            st.caption(
                f"{format_inr(amount)} • "
                f"{frequency.capitalize()}"
            )


            if st.button(
                "▶️ Activate",
                key=f"activate_{recurring_id}",
                use_container_width=True,
            ):

                try:

                    activate_recurring_transaction(
                        recurring_id
                    )

                    st.success(
                        "Recurring transaction activated."
                    )

                    st.rerun()

                except Exception:

                    st.error(
                        "Recurring transaction could not be activated."
                    )


# =========================================================
# INFORMATION
# =========================================================

st.divider()

st.markdown(
    "### ℹ️ How Recurring Transactions Work"
)

st.info(
    """
    **Recurring transactions are templates for regular financial activity.**

    • Income, expenses, and internal transfers are supported.  
    • Each recurring item has its own frequency and next due date.  
    • Internal transfers move money between accounts and are not expenses.  
    • Deactivating an item preserves its configuration instead of deleting it.  
    • "Auto Create" stores your preference for automatic processing.  
    • Due transactions are identified using their next due date.

    **Important:** A recurring definition is not itself a financial
    transaction. Your actual ledger should only change when a transaction
    is explicitly created/processed.
    """
)

st.caption(
    "🔐 Financial records remain separate from recurring transaction templates."
)