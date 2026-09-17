import streamlit as st
from datetime import date
from decimal import Decimal, InvalidOperation

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)

from database.queries import get_table
from services.budget_service import (
    get_all_budgets,
    create_budget,
    update_budget,
    delete_budget,
    get_category_expense_total,
    get_budget_status,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Budgets",
    "💰",
    "wide",
)

require_login()

show_app_header(
    "Budgets",
    "Set monthly spending limits and track your category-wise spending.",
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


def get_categories() -> list[dict]:
    """Return active expense categories."""

    response = (
        get_table("categories")
        .select(
            "id,name,category_type,is_active"
        )
        .eq(
            "is_active",
            True,
        )
        .eq(
            "category_type",
            "expense",
        )
        .order(
            "name"
        )
        .execute()
    )

    return response.data or []


def get_month_range(
    month: int,
    year: int,
) -> tuple[date, date]:
    """Return first and last date of a month."""

    start_date = date(
        year,
        month,
        1,
    )

    if month == 12:

        next_month = date(
            year + 1,
            1,
            1,
        )

    else:

        next_month = date(
            year,
            month + 1,
            1,
        )

    end_date = next_month.fromordinal(
        next_month.toordinal() - 1
    )

    return start_date, end_date


# =========================================================
# LOAD DATA
# =========================================================

categories = get_categories()

category_map = {
    category["id"]: category["name"]
    for category in categories
}


# =========================================================
# MONTH SELECTION
# =========================================================

st.markdown("## 📅 Budget Period")

month_col1, month_col2 = st.columns(2)

with month_col1:

    selected_date = st.date_input(
        "Select month",
        value=date.today().replace(day=1),
    )

selected_month = selected_date.month
selected_year = selected_date.year

month_name = selected_date.strftime(
    "%B %Y"
)

with month_col2:

    st.info(
        f"Managing budgets for **{month_name}**"
    )


st.divider()


# =========================================================
# CREATE BUDGET
# =========================================================

st.markdown("## ➕ Create Budget")

st.caption(
    "Set a monthly spending limit for an expense category."
)

if not categories:

    st.warning(
        "No active expense categories are available."
    )

else:

    with st.form(
        "create_budget_form",
        clear_on_submit=True,
    ):

        category_id = st.selectbox(
            "Expense Category",
            options=[
                category["id"]
                for category in categories
            ],
            format_func=lambda value: category_map[value],
        )

        amount_text = st.text_input(
            "Monthly Budget Amount",
            placeholder="Example: 5000",
        )

        create_button = st.form_submit_button(
            "💰 Create Budget",
            use_container_width=True,
            type="primary",
        )


    if create_button:

        if not amount_text.strip():

            st.error(
                "Please enter a budget amount."
            )

        else:

            try:

                amount = Decimal(
                    amount_text.strip()
                )

                if amount <= Decimal("0.00"):

                    st.error(
                        "Budget amount must be greater than ₹0."
                    )

                else:

                    try:

                        create_budget(
                            category_id=category_id,
                            month=selected_month,
                            year=selected_year,
                            amount=amount,
                        )

                        st.success(
                            f"Budget created for "
                            f"{category_map[category_id]}."
                        )

                        st.rerun()

                    except ValueError as exc:

                        st.error(
                            str(exc)
                        )

                    except Exception:

                        st.error(
                            "Could not create the budget. "
                            "Please try again."
                        )

            except InvalidOperation:

                st.error(
                    "Please enter a valid numeric amount."
                )


st.divider()


# =========================================================
# LOAD CURRENT BUDGETS
# =========================================================

st.markdown(
    f"## 📊 {month_name} Budget Overview"
)

try:

    budgets = get_all_budgets(
        month=selected_month,
        year=selected_year,
    )

except Exception:

    st.error(
        "Budgets could not be loaded."
    )

    st.stop()


# =========================================================
# EMPTY STATE
# =========================================================

if not budgets:

    st.info(
        f"No budgets have been created for {month_name} yet."
    )

    st.markdown(
        """
        **How to get started**

        1. Select an expense category above.
        2. Enter your monthly spending limit.
        3. Click **Create Budget**.
        4. Your actual spending will automatically be compared against it.
        """
    )

    st.stop()


# =========================================================
# CALCULATE BUDGET STATISTICS
# =========================================================

start_date, end_date = get_month_range(
    selected_month,
    selected_year,
)

budget_results = []

total_budget = Decimal("0.00")
total_spent = Decimal("0.00")

for budget in budgets:

    category_id = budget.get(
        "category_id"
    )

    category_name = category_map.get(
        category_id,
        "Unknown Category",
    )

    budget_amount = money(
        budget.get(
            "budget_amount"
        )
    )

    spent = get_category_expense_total(
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
    )

    status = get_budget_status(
        budget=budget,
        spent=spent,
    )

    total_budget += status["budget_amount"]
    total_spent += status["spent"]

    budget_results.append(
        {
            "budget": budget,
            "category_id": category_id,
            "category_name": category_name,
            "status": status,
        }
    )


total_remaining = (
    total_budget - total_spent
)

if total_budget > Decimal("0.00"):

    total_percentage = (
        total_spent / total_budget
    ) * Decimal("100")

else:

    total_percentage = Decimal("0.00")


# =========================================================
# SUMMARY CARDS
# =========================================================

summary1, summary2, summary3, summary4 = st.columns(4)

with summary1:

    st.metric(
        "Total Budget",
        format_inr(total_budget),
    )

with summary2:

    st.metric(
        "Total Spent",
        format_inr(total_spent),
    )

with summary3:

    if total_remaining >= Decimal("0.00"):

        st.metric(
            "Remaining",
            format_inr(total_remaining),
        )

    else:

        st.metric(
            "Over Budget",
            format_inr(abs(total_remaining)),
        )

with summary4:

    st.metric(
        "Overall Usage",
        f"{total_percentage:.1f}%",
    )


st.divider()


# =========================================================
# BUDGET CARDS
# =========================================================

st.markdown("### 📋 Category Budgets")


for index, item in enumerate(
    budget_results
):

    budget = item["budget"]
    category_name = item["category_name"]
    status = item["status"]

    budget_id = budget["id"]

    budget_amount = status[
        "budget_amount"
    ]

    spent = status["spent"]

    remaining = status[
        "remaining"
    ]

    percentage = status[
        "percentage"
    ]

    exceeded = status[
        "exceeded"
    ]


    # -----------------------------------------------------
    # CATEGORY HEADER
    # -----------------------------------------------------

    st.markdown(
        f"#### 🏷️ {category_name}"
    )


    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Budget",
            format_inr(
                budget_amount
            ),
        )

    with col2:

        st.metric(
            "Spent",
            format_inr(
                spent
            ),
        )

    with col3:

        if remaining >= Decimal("0.00"):

            st.metric(
                "Remaining",
                format_inr(
                    remaining
                ),
            )

        else:

            st.metric(
                "Over Budget",
                format_inr(
                    abs(remaining)
                ),
            )


    # -----------------------------------------------------
    # PROGRESS
    # -----------------------------------------------------

    progress = float(
        min(
            max(
                percentage,
                Decimal("0.00"),
            ),
            Decimal("100.00"),
        )
        / Decimal("100.00")
    )

    st.progress(
        progress
    )

    st.caption(
        f"{percentage:.1f}% of budget used"
    )


    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if exceeded:

        st.error(
            f"🚨 Budget exceeded by "
            f"{format_inr(abs(remaining))}."
        )

    elif percentage >= Decimal("80.00"):

        st.warning(
            f"⚠️ {percentage:.1f}% of this budget has been used."
        )

    else:

        st.success(
            f"✅ {percentage:.1f}% of this budget has been used."
        )


    # -----------------------------------------------------
    # EDIT / DELETE
    # -----------------------------------------------------

    with st.expander(
        "⚙️ Manage Budget"
    ):

        new_amount_text = st.text_input(
            "New Budget Amount",
            value=f"{budget_amount:.2f}",
            key=f"budget_amount_{budget_id}",
        )

        manage_col1, manage_col2 = st.columns(2)

        with manage_col1:

            if st.button(
                "💾 Update",
                key=f"update_{budget_id}",
                use_container_width=True,
            ):

                try:

                    new_amount = Decimal(
                        new_amount_text.strip()
                    )

                    if new_amount <= Decimal("0.00"):

                        st.error(
                            "Budget must be greater than ₹0."
                        )

                    else:

                        update_budget(
                            budget_id=budget_id,
                            amount=new_amount,
                        )

                        st.success(
                            "Budget updated successfully."
                        )

                        st.rerun()

                except InvalidOperation:

                    st.error(
                        "Enter a valid numeric amount."
                    )

                except Exception:

                    st.error(
                        "Budget could not be updated."
                    )


        with manage_col2:

            if st.button(
                "🗑️ Delete",
                key=f"delete_{budget_id}",
                use_container_width=True,
            ):

                st.session_state[
                    f"confirm_delete_{budget_id}"
                ] = True


        if st.session_state.get(
            f"confirm_delete_{budget_id}",
            False,
        ):

            st.warning(
                f"Delete the {category_name} budget "
                f"for {month_name}?"
            )

            confirm_col1, confirm_col2 = st.columns(2)

            with confirm_col1:

                if st.button(
                    "Yes, Delete",
                    key=f"confirm_yes_{budget_id}",
                    use_container_width=True,
                    type="primary",
                ):

                    try:

                        delete_budget(
                            budget_id
                        )

                        st.session_state.pop(
                            f"confirm_delete_{budget_id}",
                            None,
                        )

                        st.success(
                            "Budget deleted successfully."
                        )

                        st.rerun()

                    except Exception:

                        st.error(
                            "Budget could not be deleted."
                        )

            with confirm_col2:

                if st.button(
                    "Cancel",
                    key=f"confirm_no_{budget_id}",
                    use_container_width=True,
                ):

                    st.session_state.pop(
                        f"confirm_delete_{budget_id}",
                        None,
                    )

                    st.rerun()


    st.divider()


# =========================================================
# FINANCIAL RULE
# =========================================================

st.markdown("### ℹ️ Budget Calculation")

st.info(
    """
    Budget usage is calculated from **expense transactions only**.

    • Income does not consume a budget.  
    • Internal transfers do not consume a budget.  
    • Friend money transactions do not consume a budget.  
    • Savings-goal contributions are not treated as ordinary expenses.  
    • Budgets do not change your actual account balance.
    """
)


st.caption(
    "💡 A budget is a spending limit for planning purposes; your transaction records remain the source of truth."
)