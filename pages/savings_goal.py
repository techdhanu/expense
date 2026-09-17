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
    get_savings_goal,
    create_savings_goal,
    get_goal_status,
    contribute_to_savings_goal,
    update_savings_goal,
    cancel_savings_goal,
)

from services.account_service import (
    get_all_accounts,
)

from database.queries import get_table


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
    """Safely convert a value to Decimal."""
    return Decimal(str(value or "0.00"))


def format_inr(value) -> str:
    """Format a value as INR."""
    return f"₹{money(value):,.2f}"


def get_active_accounts() -> list[dict]:
    """Return active accounts."""
    return get_all_accounts()


# =========================================================
# LOAD ACCOUNTS
# =========================================================

try:

    accounts = get_active_accounts()

except Exception:

    st.error(
        "Accounts could not be loaded."
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
        height=90,
    )

    create_goal_button = st.form_submit_button(
        "🎯 Create Savings Goal",
        use_container_width=True,
        type="primary",
    )


if create_goal_button:

    if not goal_name.strip():

        st.error(
            "Please enter a savings goal name."
        )

    elif not target_amount_text.strip():

        st.error(
            "Please enter a target amount."
        )

    else:

        try:

            target_amount = Decimal(
                target_amount_text.strip()
            )

            if target_amount <= Decimal("0.00"):

                st.error(
                    "Target amount must be greater than ₹0."
                )

            else:

                try:

                    create_savings_goal(
                        name=goal_name,
                        target_amount=target_amount,
                        target_date=target_date,
                        notes=notes,
                    )

                    st.success(
                        f"Savings goal '{goal_name.strip()}' "
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

        except InvalidOperation:

            st.error(
                "Please enter a valid numeric target amount."
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
        "Savings goals could not be loaded."
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

    status = get_goal_status(
        goal["id"]
    )

    total_target += status[
        "target_amount"
    ]

    total_saved += status[
        "contributed"
    ]


total_remaining = max(
    total_target - total_saved,
    Decimal("0.00"),
)


if total_target > Decimal("0.00"):

    overall_percentage = (
        total_saved / total_target
    ) * Decimal("100")

else:

    overall_percentage = Decimal("0.00")


overall_percentage = min(
    overall_percentage,
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

        status = get_goal_status(
            goal_id
        )

        target = status[
            "target_amount"
        ]

        contributed = status[
            "contributed"
        ]

        remaining = status[
            "remaining"
        ]

        percentage = status[
            "percentage"
        ]


        # -------------------------------------------------
        # GOAL HEADER
        # -------------------------------------------------

        st.markdown(
            f"#### 🎯 {status['name']}"
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
                        key=f"contribution_date_{goal_id}",
                    )

                    contribution_notes = st.text_area(
                        "Notes",
                        placeholder="Optional",
                        key=f"contribution_notes_{goal_id}",
                    )

                    contribute_button = st.form_submit_button(
                        "💰 Add Contribution",
                        use_container_width=True,
                        type="primary",
                    )


                if contribute_button:

                    if not contribution_amount_text.strip():

                        st.error(
                            "Please enter a contribution amount."
                        )

                    else:

                        try:

                            contribution_amount = Decimal(
                                contribution_amount_text.strip()
                            )

                            if contribution_amount <= Decimal("0.00"):

                                st.error(
                                    "Contribution must be greater than ₹0."
                                )

                            elif (
                                contribution_amount
                                > remaining
                            ):

                                st.warning(
                                    f"This contribution is larger "
                                    f"than the remaining goal amount "
                                    f"of {format_inr(remaining)}."
                                )

                            else:

                                try:

                                    contribute_to_savings_goal(
                                        goal_id=goal_id,
                                        account_id=contribution_account,
                                        amount=contribution_amount,
                                        contribution_date=contribution_date,
                                        notes=contribution_notes,
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
                                        "Contribution could not be recorded."
                                    )

                        except InvalidOperation:

                            st.error(
                                "Please enter a valid numeric amount."
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
                    key=f"edit_date_{goal_id}",
                )

            else:

                edit_target_date = None


            edit_notes = st.text_area(
                "Notes",
                value=goal.get("notes") or "",
                key=f"edit_notes_{goal_id}",
            )


            if st.button(
                "💾 Save Changes",
                key=f"save_goal_{goal_id}",
                use_container_width=True,
            ):

                if not edit_name.strip():

                    st.error(
                        "Goal name cannot be empty."
                    )

                elif not edit_target_text.strip():

                    st.error(
                        "Target amount is required."
                    )

                else:

                    try:

                        new_target = Decimal(
                            edit_target_text.strip()
                        )

                        if new_target <= Decimal("0.00"):

                            st.error(
                                "Target amount must be greater than ₹0."
                            )

                        elif (
                            new_target
                            < contributed
                        ):

                            st.error(
                                f"Target amount cannot be lower "
                                f"than the already contributed "
                                f"amount of {format_inr(contributed)}."
                            )

                        else:

                            update_savings_goal(
                                goal_id,
                                {
                                    "name": edit_name,
                                    "target_amount": new_target,
                                    "target_date": edit_target_date,
                                    "notes": edit_notes,
                                },
                            )

                            st.success(
                                "Savings goal updated successfully."
                            )

                            st.rerun()

                    except InvalidOperation:

                        st.error(
                            "Please enter a valid target amount."
                        )

                    except ValueError as exc:

                        st.error(
                            str(exc)
                        )

                    except Exception:

                        st.error(
                            "Savings goal could not be updated."
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
                    f"'{status['name']}'?"
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
                                "Savings goal could not be cancelled."
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

        status = get_goal_status(
            goal["id"]
        )

        st.success(
            f"🏆 **{status['name']}** — "
            f"{format_inr(status['contributed'])} saved "
            f"of {format_inr(status['target_amount'])}"
        )


# =========================================================
# CANCELLED GOALS
# =========================================================

if cancelled_goals:

    with st.expander(
        f"🚫 Cancelled Goals ({len(cancelled_goals)})"
    ):

        for goal in cancelled_goals:

            status = get_goal_status(
                goal["id"]
            )

            st.write(
                f"**{status['name']}** — "
                f"{format_inr(status['contributed'])} contributed "
                f"of {format_inr(status['target_amount'])}"
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
    "🎯 Savings goals help you plan where your money is going without changing the underlying financial record."
)