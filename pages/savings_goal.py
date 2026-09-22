import streamlit as st
from datetime import date
from decimal import Decimal, InvalidOperation

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)

from services.savings_service import (
    get_all_savings_goals,
    create_savings_goal,
    get_goal_status,
    contribute_to_savings_goal,
    update_savings_goal,
    cancel_savings_goal,
)

from services.account_service import (
    get_all_accounts,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Savings Goals",
    "🎯",
    "wide",
)

require_login()

show_app_header(
    "Savings Goals",
    "Create goals, contribute money, and track your progress.",
)


# =========================================================
# HELPERS
# =========================================================

def money(value) -> Decimal:
    """
    Safely convert a value to Decimal.

    Financial calculations on this page always remain Decimal-based.
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
    """Format a value as INR."""

    return f"₹{money(value):,.2f}"


def parse_positive_amount(
    value: str,
    field_name: str,
) -> Decimal:
    """
    Parse and validate a positive monetary amount.
    """

    clean_value = (
        value or ""
    ).strip()


    if not clean_value:

        raise ValueError(
            f"Please enter a {field_name}."
        )


    try:

        amount = Decimal(
            clean_value
        )

    except (InvalidOperation, ValueError, TypeError):

        raise ValueError(
            f"Please enter a valid {field_name}."
        )


    if not amount.is_finite():

        raise ValueError(
            f"Please enter a valid {field_name}."
        )


    if amount <= Decimal("0.00"):

        raise ValueError(
            f"{field_name.capitalize()} "
            "must be greater than ₹0."
        )


    return amount


def get_active_accounts() -> list[dict]:
    """
    Return active accounts.

    account_service already handles user isolation and
    active-account filtering.
    """

    return get_all_accounts()


# =========================================================
# LOAD ACCOUNTS
# =========================================================

try:

    accounts = get_active_accounts()

except Exception:

    st.error(
        "Accounts could not be loaded. "
        "Please try again."
    )

    st.stop()


account_map = {
    account["id"]: account["name"]
    for account in accounts
}


# =========================================================
# CREATE NEW SAVINGS GOAL
# =========================================================

st.markdown("## ➕ Create Savings Goal")

st.caption(
    "Define a target and optionally set a date to achieve it."
)


with st.form(
    "create_savings_goal_form",
    clear_on_submit=True,
):

    goal_name = st.text_input(
        "Goal Name",
        placeholder="Example: New Laptop",
        max_chars=100,
    )


    target_amount_text = st.text_input(
        "Target Amount",
        placeholder="Example: 80000",
    )


    target_date_enabled = st.checkbox(
        "Set a target date",
        value=False,
    )


    if target_date_enabled:

        target_date = st.date_input(
            "Target Date",
            value=date.today(),
            min_value=date.today(),
        )

    else:

        target_date = None


    notes = st.text_area(
        "Notes",
        placeholder="Optional notes about this goal...",
        max_chars=1000,
        height=90,
    )


    create_goal_button = st.form_submit_button(
        "🎯 Create Savings Goal",
        use_container_width=True,
        type="primary",
    )


if create_goal_button:

    clean_goal_name = (
        goal_name or ""
    ).strip()


    if not clean_goal_name:

        st.error(
            "Please enter a savings goal name."
        )

    else:

        try:

            target_amount = parse_positive_amount(
                target_amount_text,
                "target amount",
            )

        except ValueError as exc:

            st.error(
                str(exc)
            )

        else:

            try:

                create_savings_goal(
                    name=clean_goal_name,
                    target_amount=target_amount,
                    target_date=target_date,
                    notes=(
                        notes.strip()
                        if notes
                        else None
                    ),
                )


                st.success(
                    f"Savings goal '{clean_goal_name}' "
                    "created successfully."
                )


                st.rerun()


            except ValueError as exc:

                st.error(
                    str(exc)
                )


            except Exception:

                st.error(
                    "Savings goal could not be created. "
                    "Please try again."
                )


st.divider()


# =========================================================
# LOAD SAVINGS GOALS
# =========================================================

st.markdown("## 🎯 Your Savings Goals")


try:

    goals = get_all_savings_goals(
        include_inactive=True
    )

except Exception:

    st.error(
        "Savings goals could not be loaded. "
        "Please try again."
    )

    st.stop()


# =========================================================
# EMPTY STATE
# =========================================================

if not goals:

    st.info(
        "You haven't created any savings goals yet."
    )


    st.markdown(
        """
        **Get started:**

        1. Enter a goal name.
        2. Set your target amount.
        3. Optionally choose a target date.
        4. Create the goal.
        5. Add contributions as you save.
        """
    )

    st.stop()


# =========================================================
# OVERALL STATISTICS
# =========================================================

active_goals = [
    goal
    for goal in goals
    if goal.get("status") == "active"
]


completed_goals = [
    goal
    for goal in goals
    if goal.get("status") == "completed"
]


cancelled_goals = [
    goal
    for goal in goals
    if goal.get("status") == "cancelled"
]


total_target = Decimal("0.00")
total_saved = Decimal("0.00")


for goal in active_goals:

    try:

        status = get_goal_status(
            goal["id"]
        )

    except Exception:

        st.error(
            "Unable to calculate savings-goal progress. "
            "Please try again."
        )

        st.stop()


    total_target += money(
        status.get(
            "target_amount",
            "0.00",
        )
    )


    total_saved += money(
        status.get(
            "contributed",
            "0.00",
        )
    )


total_remaining = max(
    total_target - total_saved,
    Decimal("0.00"),
)


if total_target > Decimal("0.00"):

    overall_percentage = (
        total_saved
        / total_target
    ) * Decimal("100")

else:

    overall_percentage = Decimal("0.00")


overall_percentage = min(
    max(
        overall_percentage,
        Decimal("0.00"),
    ),
    Decimal("100.00"),
)


# =========================================================
# SUMMARY
# =========================================================

summary1, summary2, summary3, summary4 = st.columns(4)


with summary1:

    st.metric(
        "Active Goals",
        len(active_goals),
    )


with summary2:

    st.metric(
        "Total Target",
        format_inr(total_target),
    )


with summary3:

    st.metric(
        "Total Saved",
        format_inr(total_saved),
    )


with summary4:

    st.metric(
        "Overall Progress",
        f"{overall_percentage:.1f}%",
    )


st.divider()


# =========================================================
# ACTIVE GOALS
# =========================================================

st.markdown("### 🚀 Active Goals")


if not active_goals:

    st.info(
        "There are currently no active savings goals."
    )

else:

    for goal in active_goals:

        goal_id = goal["id"]


        try:

            status = get_goal_status(
                goal_id
            )

        except Exception:

            st.error(
                "Unable to calculate this goal's progress."
            )

            continue


        target = money(
            status.get(
                "target_amount",
                "0.00",
            )
        )


        contributed = money(
            status.get(
                "contributed",
                "0.00",
            )
        )


        remaining = money(
            status.get(
                "remaining",
                target - contributed,
            )
        )


        percentage = money(
            status.get(
                "percentage",
                "0.00",
            )
        )


        percentage = min(
            max(
                percentage,
                Decimal("0.00"),
            ),
            Decimal("100.00"),
        )


        # -------------------------------------------------
        # GOAL HEADER
        # -------------------------------------------------

        st.markdown(
            f"#### 🎯 {status.get('name', goal.get('name', 'Savings Goal'))}"
        )


        # -------------------------------------------------
        # TARGET DATE
        # -------------------------------------------------

        goal_target_date = goal.get(
            "target_date"
        )


        if goal_target_date:

            try:

                target_date_value = date.fromisoformat(
                    str(goal_target_date)[:10]
                )


                if target_date_value < date.today():

                    st.warning(
                        f"⚠️ Target date: "
                        f"{target_date_value.strftime('%d %B %Y')} "
                        f"— target date has passed."
                    )

                else:

                    days_remaining = (
                        target_date_value
                        - date.today()
                    ).days


                    st.caption(
                        f"📅 Target date: "
                        f"{target_date_value.strftime('%d %B %Y')} "
                        f"• {days_remaining} days remaining"
                    )


            except ValueError:

                st.caption(
                    f"📅 Target date: {goal_target_date}"
                )

        else:

            st.caption(
                "📅 No target date set"
            )


        # -------------------------------------------------
        # GOAL METRICS
        # -------------------------------------------------

        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "Target",
                format_inr(target),
            )


        with col2:

            st.metric(
                "Saved",
                format_inr(contributed),
            )


        with col3:

            st.metric(
                "Remaining",
                format_inr(remaining),
            )


        # -------------------------------------------------
        # PROGRESS BAR
        # -------------------------------------------------

        progress = float(
            percentage
            / Decimal("100.00")
        )


        st.progress(
            progress
        )


        st.caption(
            f"{percentage:.1f}% completed"
        )


        # -------------------------------------------------
        # STATUS MESSAGE
        # -------------------------------------------------

        if remaining <= Decimal("0.00"):

            st.success(
                "🎉 This goal has reached its target!"
            )

        elif percentage >= Decimal("80.00"):

            st.info(
                f"🔥 Almost there! Only "
                f"{format_inr(remaining)} remaining."
            )

        elif percentage > Decimal("0.00"):

            st.success(
                f"You're making progress. "
                f"{format_inr(remaining)} left to reach the goal."
            )

        else:

            st.warning(
                "No contributions have been made yet."
            )


        # =================================================
        # CONTRIBUTE
        # =================================================

        with st.expander(
            "💸 Add Contribution"
        ):

            if not accounts:

                st.warning(
                    "No active accounts are available."
                )

            else:

                with st.form(
                    f"contribution_form_{goal_id}"
                ):

                    contribution_account = st.selectbox(
                        "Source Account",
                        options=[
                            account["id"]
                            for account in accounts
                        ],
                        format_func=lambda account_id:
                            account_map[account_id],
                        key=f"contribution_account_{goal_id}",
                    )


                    contribution_amount_text = st.text_input(
                        "Contribution Amount",
                        placeholder="Example: 5000",
                        key=f"contribution_amount_{goal_id}",
                    )


                    contribution_date = st.date_input(
                        "Contribution Date",
                        value=date.today(),
                        max_value=date.today(),
                        key=f"contribution_date_{goal_id}",
                    )


                    contribution_notes = st.text_area(
                        "Notes",
                        placeholder="Optional",
                        max_chars=1000,
                        key=f"contribution_notes_{goal_id}",
                    )


                    contribute_button = st.form_submit_button(
                        "💰 Add Contribution",
                        use_container_width=True,
                        type="primary",
                    )


                if contribute_button:

                    try:

                        contribution_amount = parse_positive_amount(
                            contribution_amount_text,
                            "contribution amount",
                        )


                        if contribution_amount > remaining:

                            st.warning(
                                f"This contribution is larger "
                                f"than the remaining goal amount "
                                f"of {format_inr(remaining)}."
                            )

                        else:

                            contribute_to_savings_goal(
                                goal_id=goal_id,
                                account_id=contribution_account,
                                amount=contribution_amount,
                                contribution_date=contribution_date,
                                notes=(
                                    contribution_notes.strip()
                                    if contribution_notes
                                    else None
                                ),
                            )


                            st.success(
                                "Contribution added successfully."
                            )


                            st.rerun()


                    except ValueError as exc:

                        st.error(
                            str(exc)
                        )


                    except Exception:

                        st.error(
                            "Contribution could not be recorded. "
                            "Please try again."
                        )


        # =================================================
        # EDIT GOAL
        # =================================================

        with st.expander(
            "✏️ Edit Goal"
        ):

            edit_name = st.text_input(
                "Goal Name",
                value=goal.get("name", ""),
                max_chars=100,
                key=f"edit_name_{goal_id}",
            )


            edit_target_text = st.text_input(
                "Target Amount",
                value=f"{target:.2f}",
                key=f"edit_target_{goal_id}",
            )


            existing_target_date = goal.get(
                "target_date"
            )


            if existing_target_date:

                try:

                    edit_target_date = date.fromisoformat(
                        str(existing_target_date)[:10]
                    )

                except ValueError:

                    edit_target_date = date.today()

            else:

                edit_target_date = date.today()


            edit_target_date_enabled = st.checkbox(
                "Use target date",
                value=bool(existing_target_date),
                key=f"edit_date_enabled_{goal_id}",
            )


            if edit_target_date_enabled:

                edit_target_date = st.date_input(
                    "Target Date",
                    value=edit_target_date,
                    min_value=date.today(),
                    key=f"edit_date_{goal_id}",
                )

            else:

                edit_target_date = None


            edit_notes = st.text_area(
                "Notes",
                value=goal.get("notes") or "",
                max_chars=1000,
                key=f"edit_notes_{goal_id}",
            )


            if st.button(
                "💾 Save Changes",
                key=f"save_goal_{goal_id}",
                use_container_width=True,
            ):

                clean_edit_name = (
                    edit_name or ""
                ).strip()


                if not clean_edit_name:

                    st.error(
                        "Goal name cannot be empty."
                    )

                elif not edit_target_text.strip():

                    st.error(
                        "Target amount is required."
                    )

                else:

                    try:

                        new_target = parse_positive_amount(
                            edit_target_text,
                            "target amount",
                        )


                        if new_target < contributed:

                            st.error(
                                f"Target amount cannot be lower "
                                f"than the already contributed "
                                f"amount of {format_inr(contributed)}."
                            )

                        else:

                            update_savings_goal(
                                goal_id,
                                {
                                    "name": clean_edit_name,
                                    "target_amount": new_target,
                                    "target_date": edit_target_date,
                                    "notes": edit_notes.strip(),
                                },
                            )


                            st.success(
                                "Savings goal updated successfully."
                            )


                            st.rerun()


                    except ValueError as exc:

                        st.error(
                            str(exc)
                        )


                    except Exception:

                        st.error(
                            "Savings goal could not be updated. "
                            "Please try again."
                        )


        # =================================================
        # CANCEL GOAL
        # =================================================

        with st.expander(
            "⚙️ Goal Management"
        ):

            st.warning(
                "Cancelling a goal keeps its contribution "
                "history but marks the goal as cancelled."
            )


            if st.button(
                "🚫 Cancel Goal",
                key=f"cancel_goal_{goal_id}",
                use_container_width=True,
            ):

                st.session_state[
                    f"confirm_cancel_{goal_id}"
                ] = True


            if st.session_state.get(
                f"confirm_cancel_{goal_id}",
                False,
            ):

                st.warning(
                    f"Are you sure you want to cancel "
                    f"'{status.get('name', goal.get('name', 'this goal'))}'?"
                )


                confirm1, confirm2 = st.columns(2)


                with confirm1:

                    if st.button(
                        "Yes, Cancel",
                        key=f"confirm_cancel_yes_{goal_id}",
                        use_container_width=True,
                        type="primary",
                    ):

                        try:

                            cancel_savings_goal(
                                goal_id
                            )


                            st.session_state.pop(
                                f"confirm_cancel_{goal_id}",
                                None,
                            )


                            st.success(
                                "Savings goal cancelled."
                            )


                            st.rerun()


                        except Exception:

                            st.error(
                                "Savings goal could not be cancelled. "
                                "Please try again."
                            )


                with confirm2:

                    if st.button(
                        "Keep Goal",
                        key=f"confirm_cancel_no_{goal_id}",
                        use_container_width=True,
                    ):

                        st.session_state.pop(
                            f"confirm_cancel_{goal_id}",
                            None,
                        )


                        st.rerun()


        st.divider()


# =========================================================
# COMPLETED GOALS
# =========================================================

if completed_goals:

    st.markdown("### 🏆 Completed Goals")


    for goal in completed_goals:

        try:

            status = get_goal_status(
                goal["id"]
            )

        except Exception:

            st.warning(
                "Unable to load a completed goal."
            )

            continue


        st.success(
            f"🏆 **{status.get('name', goal.get('name', 'Savings Goal'))}** — "
            f"{format_inr(status.get('contributed', '0.00'))} saved "
            f"of {format_inr(status.get('target_amount', '0.00'))}"
        )


# =========================================================
# CANCELLED GOALS
# =========================================================

if cancelled_goals:

    with st.expander(
        f"🚫 Cancelled Goals ({len(cancelled_goals)})"
    ):

        for goal in cancelled_goals:

            try:

                status = get_goal_status(
                    goal["id"]
                )

            except Exception:

                st.warning(
                    "Unable to load a cancelled goal."
                )

                continue


            st.write(
                f"**{status.get('name', goal.get('name', 'Savings Goal'))}** — "
                f"{format_inr(status.get('contributed', '0.00'))} contributed "
                f"of {format_inr(status.get('target_amount', '0.00'))}"
            )


# =========================================================
# FINANCIAL RULE
# =========================================================

st.divider()

st.markdown("### ℹ️ How Savings Goals Work")

st.info(
    """
    **Savings contributions are recorded as real transactions.**

    • The selected source account decreases by the contribution amount.  
    • The contribution is linked to the savings goal.  
    • Savings contributions are tracked separately from ordinary expenses.  
    • Reaching the target automatically marks the goal as completed.  
    • Cancelling a goal preserves its contribution history.  
    • Your actual account balance remains the source of truth.
    """
)


st.caption(
    "🎯 Savings goals help you plan where your money is going "
    "without changing the underlying financial record."
)