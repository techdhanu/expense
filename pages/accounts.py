import streamlit as st
from decimal import Decimal, InvalidOperation

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)

from services.account_service import (
    get_all_accounts,
    get_all_account_balances,
    create_account,
    deactivate_account,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Accounts",
    "🏦",
    "wide",
)

require_login()


# =========================================================
# PAGE HEADER
# =========================================================

show_app_header(
    "Accounts",
    "Manage your accounts and monitor their current balances.",
)


# =========================================================
# LOAD ACCOUNT DATA
# =========================================================

try:

    accounts = get_all_accounts()

    account_balances = get_all_account_balances()

except Exception as exc:

    st.error(
        f"Unable to load account information.\n\n{exc}"
    )

    st.stop()


# =========================================================
# ACCOUNT SUMMARY
# =========================================================

st.markdown("## 🏦 Account Overview")

total_accounts = len(account_balances)

total_balance = Decimal("0.00")

for account in account_balances:

    total_balance += Decimal(
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


summary_col1, summary_col2 = st.columns(2)


with summary_col1:

    st.metric(
        "Active Accounts",
        total_accounts,
    )


with summary_col2:

    st.metric(
        "Total Current Balance",
        f"₹{total_balance:,.2f}",
    )


st.divider()


# =========================================================
# CURRENT ACCOUNTS
# =========================================================

st.markdown("### 💳 Your Accounts")

if not account_balances:

    st.info(
        "You don't have any active accounts yet."
    )

else:

    for account in account_balances:

        account_id = account.get("id")

        account_name = account.get(
            "account_name",
            account.get(
                "name",
                "Account",
            ),
        )

        account_type = account.get(
            "account_type",
            "other",
        )

        current_balance = Decimal(
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

        opening_balance = Decimal(
            str(
                account.get(
                    "opening_balance",
                    "0.00",
                )
            )
        )


        # -------------------------------------------------
        # ACCOUNT CARD
        # -------------------------------------------------

        with st.container(border=True):

            header_col1, header_col2 = st.columns(
                [0.70, 0.30]
            )

            with header_col1:

                st.markdown(
                    f"### 🏦 {account_name}"
                )

                st.caption(
                    f"Account type: "
                    f"{account_type.replace('_', ' ').title()}"
                )

            with header_col2:

                st.metric(
                    "Current Balance",
                    f"₹{current_balance:,.2f}",
                )


            st.divider()


            detail_col1, detail_col2 = st.columns(2)


            with detail_col1:

                st.caption(
                    "Opening Balance"
                )

                st.markdown(
                    f"**₹{opening_balance:,.2f}**"
                )


            with detail_col2:

                st.caption(
                    "Account Status"
                )

                st.markdown(
                    "**🟢 Active**"
                )


            # -------------------------------------------------
            # DEACTIVATE ACCOUNT
            # -------------------------------------------------

            st.divider()

            with st.expander(
                "⚙️ Account Actions"
            ):

                st.warning(
                    "Deactivating an account hides it from "
                    "new transactions. Existing financial "
                    "records are preserved."
                )

                confirm_key = (
                    f"confirm_deactivate_{account_id}"
                )

                confirm = st.checkbox(
                    "I understand that this account will "
                    "no longer be available for new transactions.",
                    key=confirm_key,
                )

                if st.button(
                    "Deactivate Account",
                    key=f"deactivate_{account_id}",
                    use_container_width=True,
                ):

                    if not confirm:

                        st.error(
                            "Please confirm before "
                            "deactivating the account."
                        )

                    else:

                        try:

                            deactivate_account(
                                account_id
                            )

                            st.success(
                                f"{account_name} "
                                "was deactivated successfully."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "Account could not be deactivated.\n\n"
                                f"{exc}"
                            )


# =========================================================
# CREATE ACCOUNT
# =========================================================

st.divider()

st.markdown("## ➕ Add Account")

st.caption(
    "Create another account if you use an additional "
    "bank account, wallet, or cash account."
)


with st.container(border=True):

    account_name = st.text_input(
        "Account Name",
        placeholder="e.g. Emergency Fund",
        max_chars=100,
        key="new_account_name",
    )


    account_type_label = st.selectbox(
        "Account Type",
        options=[
            "Bank",
            "Cash",
            "Other",
        ],
        key="new_account_type",
    )


    account_type_map = {
        "Bank": "bank",
        "Cash": "cash",
        "Other": "other",
    }


    opening_balance_text = st.text_input(
        "Opening Balance (₹)",
        value="0.00",
        placeholder="0.00",
        help=(
            "Enter the balance that existed in this "
            "account when you started tracking it."
        ),
        key="new_opening_balance",
    )


    st.caption(
        "Opening balance can be ₹0.00 or a positive amount."
    )


    if st.button(
        "🏦 Create Account",
        use_container_width=True,
        type="primary",
        key="create_account_button",
    ):

        # -------------------------------------------------
        # NAME VALIDATION
        # -------------------------------------------------

        clean_name = account_name.strip()

        if not clean_name:

            st.error(
                "Please enter an account name."
            )

            st.stop()


        # -------------------------------------------------
        # OPENING BALANCE VALIDATION
        # -------------------------------------------------

        clean_balance = (
            opening_balance_text.strip()
        )

        try:

            opening_balance = Decimal(
                clean_balance
            )

        except (InvalidOperation, ValueError):

            st.error(
                "Please enter a valid opening balance."
            )

            st.stop()


        if opening_balance < Decimal("0.00"):

            st.error(
                "Opening balance cannot be negative."
            )

            st.stop()


        # -------------------------------------------------
        # CREATE ACCOUNT
        # -------------------------------------------------

        try:

            new_account = create_account(
                name=clean_name,
                account_type=account_type_map[
                    account_type_label
                ],
                opening_balance=opening_balance,
            )


            st.success(
                f"🏦 {clean_name} was created successfully."
            )


            st.caption(
                f"Account ID: `{new_account['id']}`"
            )


            st.rerun()


        except Exception as exc:

            error_text = str(exc).lower()

            if (
                "already exists" in error_text
                or "duplicate" in error_text
                or "unique" in error_text
            ):

                st.error(
                    f"An account named "
                    f"**{clean_name}** already exists."
                )

            else:

                st.error(
                    "Account could not be created.\n\n"
                    f"{exc}"
                )


# =========================================================
# ACCOUNT MANAGEMENT NOTE
# =========================================================

st.divider()

st.caption(
    "🔒 Existing account balances are calculated from "
    "the opening balance and recorded financial transactions."
)

st.caption(
    "🛡️ Deactivation preserves historical records and "
    "prevents accidental loss of financial data."
)