import streamlit as st
from datetime import date
from decimal import Decimal, InvalidOperation


# =========================================================
# CACHED DATA LOADER
# =========================================================

@st.cache_data(ttl=5, show_spinner=False)
def load_friends_money_data():
    from services.friend_money_service import (
        get_all_people,
        get_friend_money_records,
        get_money_lent_records,
        get_total_friend_money_held,
        get_total_money_lent_outstanding,
    )

    from services.account_service import (
        get_all_accounts,
    )

    return {
        "people": get_all_people(),
        "accounts": get_all_accounts(),
        "friend_records": get_friend_money_records(),
        "lent_records": get_money_lent_records(),
        "held_total": get_total_friend_money_held(),
        "lent_total": get_total_money_lent_outstanding(),
    }


from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)


from services.friend_money_service import (
    create_person,

    # Money held from friends
    record_money_received,
    record_money_returned,
    update_friend_money,

    # Money lent to friends
    record_money_lent,
    record_money_lent_returned,
    update_money_lent,
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
    "Track money you hold for others and money you've lent to others.",
)


# =========================================================
# LOAD DATA
# =========================================================

try:

    data = load_friends_money_data()

    people = data["people"]
    accounts = data["accounts"]
    friend_records = data["friend_records"]
    lent_records = data["lent_records"]
    total_held = data["held_total"]
    total_lent = data["lent_total"]

except Exception:

    st.error(
        "Unable to load friends' money data. "
        "Please try again."
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
# HELPERS
# =========================================================

def parse_amount(
    value: str,
    field_name: str,
) -> Decimal:
    """
    Safely convert user-entered amount to Decimal.
    """

    clean_value = value.strip()


    if not clean_value:

        raise ValueError(
            f"Please enter the {field_name}."
        )


    try:

        amount = Decimal(
            clean_value
        )

    except (InvalidOperation, ValueError):

        raise ValueError(
            f"Please enter a valid {field_name}."
        )


    if amount <= Decimal("0.00"):

        raise ValueError(
            f"{field_name.capitalize()} "
            "must be greater than ₹0.00."
        )


    return amount


def format_display_date(value) -> str:
    """
    Format a stored date value as a human-friendly date
    (e.g. 23 Sep 2026) for display purposes only.
    """

    if not value:

        return None

    try:

        return date.fromisoformat(
            str(value)[:10]
        ).strftime("%d %b %Y")

    except (ValueError, TypeError):

        return str(value)


# =========================================================
# PERSON SELECTION
# =========================================================

def get_person_selection(
    people_list: list[dict],
    key_prefix: str,
):
    """
    Render person selection and return:

    (
        person_id,
        person_mode,
        new_name,
        new_notes,
    )
    """

    existing_names = [
        person["name"]
        for person in people_list
    ]


    if people_list:

        person_mode = st.radio(
            "Person",
            options=[
                "Select Existing Person",
                "Create New Person",
            ],
            horizontal=True,
            key=f"{key_prefix}_person_mode",
        )

    else:

        person_mode = "Create New Person"

        st.info(
            "No people have been added yet. "
            "Create the person below."
        )


    if person_mode == "Select Existing Person":

        selected_name = st.selectbox(
            "Person",
            options=existing_names,
            key=f"{key_prefix}_person",
        )


        selected_id = next(
            person["id"]
            for person in people_list
            if person["name"] == selected_name
        )


        return (
            selected_id,
            person_mode,
            None,
            None,
        )


    new_name = st.text_input(
        "Person Name",
        placeholder="e.g. Rahul",
        max_chars=100,
        key=f"{key_prefix}_new_person_name",
    )


    new_notes = st.text_input(
        "Person Notes",
        placeholder="Optional",
        max_chars=500,
        key=f"{key_prefix}_new_person_notes",
    )


    return (
        None,
        person_mode,
        new_name,
        new_notes,
    )


# =========================================================
# CREATE PERSON IF NEEDED
# =========================================================

def create_person_if_needed(
    person_id,
    person_mode,
    new_name,
    new_notes,
):
    """
    Create a person when the form uses
    Create New Person.
    """

    if person_mode != "Create New Person":

        return person_id


    clean_name = (
        new_name or ""
    ).strip()


    if not clean_name:

        raise ValueError(
            "Please enter the person's name."
        )


    person = create_person(
        clean_name,
        (
            new_notes.strip()
            if new_notes
            else None
        ),
    )


    return person["id"]


# =========================================================
# FINANCIAL SUMMARY
# =========================================================

st.markdown("## 💰 Friends' Money Overview")


summary1, summary2, summary3 = st.columns(3)


with summary1:

    st.metric(
        "Money I Hold",
        f"₹{total_held:,.2f}",
        help=(
            "Money received from friends that "
            "you still need to return."
        ),
    )


with summary2:

    st.metric(
        "Money I Lent",
        f"₹{total_lent:,.2f}",
        help=(
            "Money you gave to friends that "
            "they still need to return."
        ),
    )


with summary3:

    net_position = (
        total_lent
        - total_held
    )


    st.metric(
        "Net Receivable",
        f"₹{net_position:,.2f}",
        help=(
            "Money others owe you minus money "
            "you owe others."
        ),
    )


st.info(
    "💡 Money you receive from friends is not income, "
    "and money you lend to friends is not an expense. "
    "Both are tracked separately from personal income and expenses."
)


# =========================================================
# MONEY I HOLD
# =========================================================

st.divider()

st.markdown("## 👥 Money I Hold")

st.caption(
    "Money someone gave you temporarily and you are expected to return."
)


# =========================================================
# CURRENT FRIEND MONEY
# =========================================================

if not friend_records:

    st.info(
        "No money-held records yet."
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


        # =================================================
        # RECORD CARD
        # =================================================

        with st.container(border=True):

            header1, header2 = st.columns(
                [0.70, 0.30]
            )


            with header1:

                st.markdown(
                    f"### 👤 {person_name}"
                )


                st.caption(
                    f"Money held in: {account_name}"
                )


            with header2:

                st.metric(
                    "Outstanding",
                    f"₹{outstanding:,.2f}",
                )


            st.divider()


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


            date1, date2 = st.columns(2)


            with date1:

                st.caption("Received Date")

                st.write(
                    format_display_date(received_date)
                    or "—"
                )


            with date2:

                st.caption("Expected Return")

                st.write(
                    format_display_date(expected_return_date)
                    or "Not specified"
                )


            # =================================================
            # RETURN MONEY
            # =================================================

            if outstanding > Decimal("0.00"):

                st.divider()


                with st.expander(
                    "↩️ Return Money"
                ):

                    return_amount_text = st.text_input(
                        "Return Amount (₹)",
                        placeholder=(
                            f"Maximum ₹{outstanding:,.2f}"
                        ),
                        key=f"held_return_amount_{record_id}",
                    )


                    return_date = st.date_input(
                        "Return Date",
                        value=date.today(),
                        max_value=date.today(),
                        key=f"held_return_date_{record_id}",
                    )


                    return_notes = st.text_input(
                        "Return Notes",
                        placeholder="Optional",
                        max_chars=500,
                        key=f"held_return_notes_{record_id}",
                    )


                    if st.button(
                        "↩️ Record Return",
                        key=f"held_return_button_{record_id}",
                        use_container_width=True,
                        type="primary",
                    ):

                        try:

                            return_amount = parse_amount(
                                return_amount_text,
                                "return amount",
                            )


                            if return_amount > outstanding:

                                raise ValueError(
                                    "Return amount cannot exceed "
                                    f"the outstanding ₹{outstanding:,.2f}."
                                )


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


                            load_friends_money_data.clear()

                            st.rerun()


                        except ValueError as exc:

                            st.error(
                                str(exc)
                            )


                        except Exception:

                            st.error(
                                "Return could not be recorded. "
                                "Please try again."
                            )


            # =================================================
            # UPDATE DETAILS
            # =================================================

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
                    key=f"held_expected_date_{record_id}",
                )


                new_notes = st.text_area(
                    "Notes",
                    value=record.get("notes") or "",
                    max_chars=1000,
                    key=f"held_notes_{record_id}",
                )


                if st.button(
                    "💾 Save Changes",
                    key=f"held_update_{record_id}",
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


                        load_friends_money_data.clear()

                        st.rerun()


                    except Exception:

                        st.error(
                            "Details could not be updated. "
                            "Please try again."
                        )


# =========================================================
# RECORD MONEY RECEIVED
# =========================================================

st.divider()


with st.expander(
    "➕ Record Money Received From Someone",
    expanded=False,
):

    st.caption(
        "Use this when someone gives you money temporarily "
        "and you are expected to return it."
    )


    (
        selected_person_id,
        person_mode,
        new_person_name,
        new_person_notes,
    ) = get_person_selection(
        people,
        "held_receive",
    )


    if not accounts:

        st.error(
            "No active accounts are available."
        )

    else:

        account_names = list(
            account_map.values()
        )


        selected_account_name = st.selectbox(
            "Account Where Money Was Received",
            options=account_names,
            key="held_receive_account",
        )


        selected_account_id = next(
            account_id
            for account_id, account_name
            in account_map.items()
            if account_name == selected_account_name
        )


        received_amount_text = st.text_input(
            "Amount Received (₹)",
            placeholder="0.00",
            key="held_receive_amount",
        )


        received_date = st.date_input(
            "Received Date",
            value=date.today(),
            max_value=date.today(),
            key="held_receive_date",
        )


        expected_return_date = st.date_input(
            "Expected Return Date",
            value=None,
            min_value=received_date,
            key="held_receive_expected_date",
            help="Optional.",
        )


        received_notes = st.text_area(
            "Notes",
            placeholder="Optional details...",
            max_chars=1000,
            height=90,
            key="held_receive_notes",
        )


        if st.button(
            "👥 Record Money Received",
            use_container_width=True,
            type="primary",
            key="record_held_money",
        ):

            try:

                selected_person_id = create_person_if_needed(
                    selected_person_id,
                    person_mode,
                    new_person_name,
                    new_person_notes,
                )


                received_amount = parse_amount(
                    received_amount_text,
                    "amount received",
                )


                record_money_received(
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


                load_friends_money_data.clear()

                st.rerun()


            except ValueError as exc:

                st.error(
                    str(exc)
                )


            except Exception:

                st.error(
                    "Friend money could not be recorded. "
                    "Please try again."
                )


# =========================================================
# MONEY I LENT
# =========================================================

st.divider()

st.markdown("## 💸 Money I Lent")

st.caption(
    "Money you gave to someone that they still need to return to you."
)


# =========================================================
# LENT SUMMARY
# =========================================================

lent_outstanding_count = 0


for record in lent_records:

    amount_lent = Decimal(
        str(
            record.get(
                "amount_lent",
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


    if (
        amount_lent
        - amount_returned
        > Decimal("0.00")
    ):

        lent_outstanding_count += 1


lent_summary1, lent_summary2 = st.columns(2)


with lent_summary1:

    st.metric(
        "Outstanding Lent",
        f"₹{total_lent:,.2f}",
    )


with lent_summary2:

    st.metric(
        "Outstanding Records",
        lent_outstanding_count,
    )


# =========================================================
# LENT RECORDS
# =========================================================

if not lent_records:

    st.info(
        "No money-lent records yet. "
        "Use the form below when you lend money to someone."
    )

else:

    for record in lent_records:

        record_id = record["id"]


        person_name = people_map.get(
            record.get("person_id"),
            "Unknown Person",
        )


        account_name = account_map.get(
            record.get("account_id"),
            "Unknown Account",
        )


        amount_lent = Decimal(
            str(
                record.get(
                    "amount_lent",
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
            amount_lent
            - amount_returned
        )


        lent_date = record.get(
            "lent_date",
            "",
        )


        expected_return_date = record.get(
            "expected_return_date"
        )


        status = record.get(
            "status",
            "lent",
        )


        # =================================================
        # LENT CARD
        # =================================================

        with st.container(border=True):

            header1, header2 = st.columns(
                [0.70, 0.30]
            )


            with header1:

                st.markdown(
                    f"### 👤 {person_name}"
                )


                st.caption(
                    f"Money lent from: {account_name}"
                )


            with header2:

                st.metric(
                    "They Owe You",
                    f"₹{outstanding:,.2f}",
                )


            st.divider()


            detail1, detail2, detail3 = st.columns(3)


            with detail1:

                st.caption("Lent")

                st.markdown(
                    f"**₹{amount_lent:,.2f}**"
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
                        "**🔴 Lent**"
                    )


            st.divider()


            date1, date2 = st.columns(2)


            with date1:

                st.caption("Lent Date")

                st.write(
                    format_display_date(lent_date)
                    or "—"
                )


            with date2:

                st.caption("Expected Return")

                st.write(
                    format_display_date(expected_return_date)
                    or "Not specified"
                )


            # =================================================
            # RECEIVE MONEY BACK
            # =================================================

            if outstanding > Decimal("0.00"):

                st.divider()


                with st.expander(
                    "💰 Receive Money Back"
                ):

                    repayment_amount_text = st.text_input(
                        "Amount Received Back (₹)",
                        placeholder=(
                            f"Maximum ₹{outstanding:,.2f}"
                        ),
                        key=f"lent_return_amount_{record_id}",
                    )


                    repayment_date = st.date_input(
                        "Return Date",
                        value=date.today(),
                        max_value=date.today(),
                        key=f"lent_return_date_{record_id}",
                    )


                    repayment_notes = st.text_input(
                        "Return Notes",
                        placeholder="Optional",
                        max_chars=500,
                        key=f"lent_return_notes_{record_id}",
                    )


                    if st.button(
                        "💰 Record Money Received Back",
                        key=f"lent_return_button_{record_id}",
                        use_container_width=True,
                        type="primary",
                    ):

                        try:

                            repayment_amount = parse_amount(
                                repayment_amount_text,
                                "repayment amount",
                            )


                            if repayment_amount > outstanding:

                                raise ValueError(
                                    "Repayment amount cannot exceed "
                                    f"the outstanding ₹{outstanding:,.2f}."
                                )


                            record_money_lent_returned(
                                money_lent_id=record_id,
                                amount=repayment_amount,
                                return_date=repayment_date,
                                notes=(
                                    repayment_notes.strip()
                                    if repayment_notes
                                    else None
                                ),
                            )


                            st.success(
                                f"₹{repayment_amount:,.2f} "
                                f"received back from {person_name}."
                            )


                            load_friends_money_data.clear()

                            st.rerun()


                        except ValueError as exc:

                            st.error(
                                str(exc)
                            )


                        except Exception:

                            st.error(
                                "Money received back could not "
                                "be recorded. Please try again."
                            )


            # =================================================
            # UPDATE LENT DETAILS
            # =================================================

            with st.expander(
                "⚙️ Update Lent Details"
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
                    key=f"lent_expected_date_{record_id}",
                )


                new_notes = st.text_area(
                    "Notes",
                    value=record.get("notes") or "",
                    max_chars=1000,
                    key=f"lent_notes_{record_id}",
                )


                if st.button(
                    "💾 Save Changes",
                    key=f"lent_update_{record_id}",
                    use_container_width=True,
                ):

                    try:

                        update_money_lent(
                            record_id,
                            {
                                "expected_return_date": (
                                    new_expected_date
                                ),
                                "notes": new_notes,
                            },
                        )


                        st.success(
                            "Lent-money details updated successfully."
                        )


                        load_friends_money_data.clear()

                        st.rerun()


                    except Exception:

                        st.error(
                            "Details could not be updated. "
                            "Please try again."
                        )


# =========================================================
# RECORD MONEY LENT
# =========================================================

st.divider()


with st.expander(
    "💸 Lend Money to Someone",
    expanded=False,
):

    st.caption(
        "Use this when you give your own money to someone "
        "and expect them to return it."
    )


    (
        selected_person_id,
        person_mode,
        new_person_name,
        new_person_notes,
    ) = get_person_selection(
        people,
        "lend_money",
    )


    if not accounts:

        st.error(
            "No active accounts are available."
        )

    else:

        selected_account_name = st.selectbox(
            "Account From Which Money Is Lent",
            options=list(account_map.values()),
            key="lend_account",
        )


        selected_account_id = next(
            account_id
            for account_id, account_name
            in account_map.items()
            if account_name == selected_account_name
        )


        lent_amount_text = st.text_input(
            "Amount Lent (₹)",
            placeholder="0.00",
            key="lend_amount",
        )


        lent_date = st.date_input(
            "Lent Date",
            value=date.today(),
            max_value=date.today(),
            key="lend_date",
        )


        expected_return_date = st.date_input(
            "Expected Return Date",
            value=None,
            min_value=lent_date,
            key="lend_expected_date",
            help="Optional.",
        )


        lent_notes = st.text_area(
            "Notes",
            placeholder="Optional details...",
            max_chars=1000,
            height=90,
            key="lend_notes",
        )


        if st.button(
            "💸 Record Money Lent",
            use_container_width=True,
            type="primary",
            key="record_lent_money",
        ):

            try:

                selected_person_id = create_person_if_needed(
                    selected_person_id,
                    person_mode,
                    new_person_name,
                    new_person_notes,
                )


                lent_amount = parse_amount(
                    lent_amount_text,
                    "amount lent",
                )


                record_money_lent(
                    person_id=selected_person_id,
                    account_id=selected_account_id,
                    amount=lent_amount,
                    lent_date=lent_date,
                    expected_return_date=(
                        expected_return_date
                        if expected_return_date
                        else None
                    ),
                    notes=(
                        lent_notes.strip()
                        if lent_notes
                        else None
                    ),
                )


                person_name = people_map.get(
                    selected_person_id,
                    "the person",
                )


                st.success(
                    f"₹{lent_amount:,.2f} lent to "
                    f"{person_name} successfully."
                )


                load_friends_money_data.clear()

                st.rerun()


            except ValueError as exc:

                st.error(
                    str(exc)
                )


            except Exception:

                st.error(
                    "Money could not be lent. "
                    "Please try again."
                )


# =========================================================
# FINANCIAL EXPLANATION
# =========================================================

st.divider()

st.markdown("### 🔐 Financial Treatment")


note1, note2 = st.columns(2)


with note1:

    st.info(
        "**Money I Hold**\n\n"
        "Someone else's money is temporarily in your account. "
        "It increases your bank balance but is not personal income."
    )


with note2:

    st.info(
        "**Money I Lent**\n\n"
        "Your money has temporarily left your account. "
        "It reduces your bank balance but is not an expense."
    )


st.caption(
    "🛡️ All returns are recorded as separate financial transactions "
    "so your financial history remains auditable."
)