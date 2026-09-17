import streamlit as st
from datetime import date
from decimal import Decimal, InvalidOperation

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)

from services.account_service import get_all_accounts

from services.friend_money_service import (
    get_all_people,
    get_total_friend_money_held,
    create_person,
    record_money_received,
    record_money_returned,
    update_friend_money,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Friends' Money",
    "👥",
    "wide",
)

require_login()


# =========================================================
# PAGE HEADER
# =========================================================

show_app_header(
    "Friends' Money",
    "Track money you're holding for others and money you've returned.",
)


# =========================================================
# LOAD DATA
# =========================================================

try:

    people = get_all_people()
    accounts = get_all_accounts()

    friend_records = (
        __import__(
            "services.friend_money_service",
            fromlist=["get_friend_money_records"],
        ).get_friend_money_records()
    )

    total_held = get_total_friend_money_held()

except Exception as exc:

    st.error(
        f"Unable to load friends' money data.\n\n{exc}"
    )

    st.stop()


# =========================================================
# LOOKUP MAPS
# =========================================================

people_map = {
    person["id"]: person["name"]
    for person in people
}

account_map = {
    account["id"]: account["name"]
    for account in accounts
}


# =========================================================
# FINANCIAL SUMMARY
# =========================================================

st.markdown("## 💰 Money Held Summary")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:

    st.metric(
        "Total Money Held",
        f"₹{Decimal(str(total_held)):,.2f}",
    )

with summary_col2:

    outstanding_count = sum(
        1
        for record in friend_records
        if (
            Decimal(str(record.get("amount_received", "0.00")))
            - Decimal(str(record.get("amount_returned", "0.00")))
        ) > Decimal("0.00")
    )

    st.metric(
        "Outstanding Records",
        outstanding_count,
    )


st.info(
    "💡 Money received from friends is not counted as income. "
    "It remains part of your bank balance, but is treated as "
    "money you owe back."
)


st.divider()


# =========================================================
# CURRENT FRIEND MONEY
# =========================================================

st.markdown("### 👥 Current Records")


if not friend_records:

    st.info(
        "No friend-money records yet. "
        "Use the form below to record money received from someone."
    )

else:

    for record in friend_records:

        record_id = record["id"]

        person_name = people_map.get(
            record.get("person_id"),
            "Unknown Person",
        )

        account_name = account_map.get(
            record.get("account_id"),
            "Unknown Account",
        )

        amount_received = Decimal(
            str(
                record.get(
                    "amount_received",
                    "0.00",
                )
            )
        )

        amount_returned = Decimal(
            str(
                record.get(
                    "amount_returned",
                    "0.00",
                )
            )
        )

        outstanding = (
            amount_received
            - amount_returned
        )

        received_date = record.get(
            "received_date",
            "",
        )

        expected_return_date = record.get(
            "expected_return_date"
        )

        status = record.get(
            "status",
            "holding",
        )


        # -------------------------------------------------
        # RECORD CARD
        # -------------------------------------------------

        with st.container(border=True):

            header_col1, header_col2 = st.columns(
                [0.70, 0.30]
            )

            with header_col1:

                st.markdown(
                    f"### 👤 {person_name}"
                )

                st.caption(
                    f"Money held in: {account_name}"
                )

            with header_col2:

                if outstanding > Decimal("0.00"):

                    st.metric(
                        "Outstanding",
                        f"₹{outstanding:,.2f}",
                    )

                else:

                    st.metric(
                        "Outstanding",
                        "₹0.00",
                    )


            st.divider()


            # -------------------------------------------------
            # DETAILS
            # -------------------------------------------------

            detail1, detail2, detail3 = st.columns(3)

            with detail1:

                st.caption("Received")

                st.markdown(
                    f"**₹{amount_received:,.2f}**"
                )

            with detail2:

                st.caption("Returned")

                st.markdown(
                    f"**₹{amount_returned:,.2f}**"
                )

            with detail3:

                st.caption("Status")

                if status == "fully_returned":

                    st.markdown(
                        "**🟢 Fully Returned**"
                    )

                elif status == "partially_returned":

                    st.markdown(
                        "**🟡 Partially Returned**"
                    )

                else:

                    st.markdown(
                        "**🔴 Holding**"
                    )


            st.divider()


            # -------------------------------------------------
            # DATES
            # -------------------------------------------------

            date_col1, date_col2 = st.columns(2)

            with date_col1:

                st.caption("Received Date")

                st.write(
                    received_date or "—"
                )

            with date_col2:

                st.caption("Expected Return")

                st.write(
                    expected_return_date
                    or "Not specified"
                )


            # -------------------------------------------------
            # RETURN MONEY
            # -------------------------------------------------

            if outstanding > Decimal("0.00"):

                st.divider()

                with st.expander(
                    "↩️ Return Money"
                ):

                    return_amount_text = st.text_input(
                        "Return Amount (₹)",
                        placeholder=f"Maximum ₹{outstanding:,.2f}",
                        key=f"return_amount_{record_id}",
                    )

                    return_date = st.date_input(
                        "Return Date",
                        value=date.today(),
                        max_value=date.today(),
                        key=f"return_date_{record_id}",
                    )

                    return_notes = st.text_input(
                        "Return Notes",
                        placeholder="Optional",
                        max_chars=500,
                        key=f"return_notes_{record_id}",
                    )


                    if st.button(
                        "↩️ Record Return",
                        key=f"return_button_{record_id}",
                        use_container_width=True,
                        type="primary",
                    ):

                        clean_amount = (
                            return_amount_text.strip()
                        )


                        if not clean_amount:

                            st.error(
                                "Please enter a return amount."
                            )

                            st.stop()


                        try:

                            return_amount = Decimal(
                                clean_amount
                            )

                        except (
                            InvalidOperation,
                            ValueError,
                        ):

                            st.error(
                                "Please enter a valid amount."
                            )

                            st.stop()


                        if return_amount <= Decimal("0.00"):

                            st.error(
                                "Return amount must be greater than ₹0.00."
                            )

                            st.stop()


                        if return_amount > outstanding:

                            st.error(
                                "Return amount cannot exceed "
                                f"the outstanding ₹{outstanding:,.2f}."
                            )

                            st.stop()


                        try:

                            record_money_returned(
                                friend_money_id=record_id,
                                amount=return_amount,
                                return_date=return_date,
                                notes=(
                                    return_notes.strip()
                                    if return_notes
                                    else None
                                ),
                            )

                            st.success(
                                f"₹{return_amount:,.2f} "
                                f"returned to {person_name}."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "Return could not be recorded.\n\n"
                                f"{exc}"
                            )


            # -------------------------------------------------
            # UPDATE DETAILS
            # -------------------------------------------------

            with st.expander(
                "⚙️ Update Details"
            ):

                current_expected = None

                if expected_return_date:

                    try:

                        current_expected = date.fromisoformat(
                            expected_return_date
                        )

                    except ValueError:

                        current_expected = None


                new_expected_date = st.date_input(
                    "Expected Return Date",
                    value=current_expected,
                    key=f"expected_date_{record_id}",
                )

                new_notes = st.text_area(
                    "Notes",
                    value=record.get("notes") or "",
                    max_chars=1000,
                    key=f"notes_{record_id}",
                )


                if st.button(
                    "💾 Save Changes",
                    key=f"update_{record_id}",
                    use_container_width=True,
                ):

                    try:

                        update_friend_money(
                            record_id,
                            {
                                "expected_return_date": (
                                    new_expected_date
                                ),
                                "notes": new_notes,
                            },
                        )

                        st.success(
                            "Details updated successfully."
                        )

                        st.rerun()

                    except Exception as exc:

                        st.error(
                            "Details could not be updated.\n\n"
                            f"{exc}"
                        )


# =========================================================
# RECORD MONEY RECEIVED
# =========================================================

st.divider()

st.markdown("## ➕ Record Money Received")

st.caption(
    "Use this when someone gives you money temporarily "
    "and you are expected to return it."
)


with st.container(border=True):

    # -----------------------------------------------------
    # PERSON
    # -----------------------------------------------------

    if people:

        existing_person_names = [
            person["name"]
            for person in people
        ]

        person_mode = st.radio(
            "Person",
            options=[
                "Select Existing Person",
                "Create New Person",
            ],
            horizontal=True,
        )

    else:

        person_mode = "Create New Person"

        st.info(
            "No people have been added yet. "
            "Create the person below."
        )


    if person_mode == "Select Existing Person":

        selected_person_name = st.selectbox(
            "Person",
            options=existing_person_names,
        )

        selected_person_id = next(
            person["id"]
            for person in people
            if person["name"]
            == selected_person_name
        )

    else:

        new_person_name = st.text_input(
            "Person Name",
            placeholder="e.g. Rahul",
            max_chars=100,
        )

        new_person_notes = st.text_input(
            "Person Notes",
            placeholder="Optional",
            max_chars=500,
        )

        selected_person_id = None


    # -----------------------------------------------------
    # ACCOUNT
    # -----------------------------------------------------

    if not accounts:

        st.error(
            "No active accounts are available."
        )

        st.stop()


    selected_account_name = st.selectbox(
        "Account Where Money Was Received",
        options=list(account_map.values()),
        help=(
            "Select the account where the friend's money "
            "was deposited or received."
        ),
    )

    selected_account_id = next(
        account_id
        for account_id, account_name
        in account_map.items()
        if account_name == selected_account_name
    )


    # -----------------------------------------------------
    # AMOUNT
    # -----------------------------------------------------

    received_amount_text = st.text_input(
        "Amount Received (₹)",
        placeholder="0.00",
    )


    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    received_date = st.date_input(
        "Received Date",
        value=date.today(),
        max_value=date.today(),
    )


    # -----------------------------------------------------
    # EXPECTED RETURN
    # -----------------------------------------------------

    expected_return_date = st.date_input(
        "Expected Return Date",
        value=None,
        min_value=received_date,
        help="Optional.",
    )


    # -----------------------------------------------------
    # NOTES
    # -----------------------------------------------------

    received_notes = st.text_area(
        "Notes",
        placeholder="Optional details...",
        max_chars=1000,
        height=90,
    )


    # -----------------------------------------------------
    # SUBMIT
    # -----------------------------------------------------

    if st.button(
        "👥 Record Money Received",
        use_container_width=True,
        type="primary",
    ):

        # -------------------------------------------------
        # PERSON VALIDATION
        # -------------------------------------------------

        if person_mode == "Create New Person":

            clean_person_name = (
                new_person_name.strip()
            )

            if not clean_person_name:

                st.error(
                    "Please enter the person's name."
                )

                st.stop()


            try:

                new_person = create_person(
                    clean_person_name,
                    (
                        new_person_notes.strip()
                        if new_person_notes
                        else None
                    ),
                )

                selected_person_id = new_person["id"]

            except Exception as exc:

                st.error(
                    f"Person could not be created.\n\n{exc}"
                )

                st.stop()


        # -------------------------------------------------
        # AMOUNT VALIDATION
        # -------------------------------------------------

        clean_amount = (
            received_amount_text.strip()
        )

        if not clean_amount:

            st.error(
                "Please enter the amount received."
            )

            st.stop()


        try:

            received_amount = Decimal(
                clean_amount
            )

        except (
            InvalidOperation,
            ValueError,
        ):

            st.error(
                "Please enter a valid amount."
            )

            st.stop()


        if received_amount <= Decimal("0.00"):

            st.error(
                "Amount must be greater than ₹0.00."
            )

            st.stop()


        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        try:

            new_record = record_money_received(
                person_id=selected_person_id,
                account_id=selected_account_id,
                amount=received_amount,
                received_date=received_date,
                expected_return_date=(
                    expected_return_date
                    if expected_return_date
                    else None
                ),
                notes=(
                    received_notes.strip()
                    if received_notes
                    else None
                ),
            )


            st.success(
                f"₹{received_amount:,.2f} "
                "was recorded successfully."
            )

            st.caption(
                f"Friend-money record ID: "
                f"`{new_record['id']}`"
            )

            st.rerun()


        except Exception as exc:

            st.error(
                "Friend money could not be recorded.\n\n"
                f"{exc}"
            )


# =========================================================
# FINANCIAL NOTE
# =========================================================

st.divider()

st.caption(
    "🔒 Friend money is tracked separately from income and "
    "expenses because it represents money that belongs to someone else."
)

st.caption(
    "🛡️ Returns are recorded as separate financial transactions "
    "and reduce the outstanding amount."
)