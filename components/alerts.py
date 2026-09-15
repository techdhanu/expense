import streamlit as st


def show_success(message: str) -> None:
    """Display a success message."""
    st.success(message)


def show_error(message: str) -> None:
    """Display an error message."""
    st.error(message)


def show_warning(message: str) -> None:
    """Display a warning message."""
    st.warning(message)


def show_info(message: str) -> None:
    """Display an informational message."""
    st.info(message)


def show_balance_alert(
    balance,
    warning_threshold=1000,
) -> None:
    """
    Show an alert when an account balance is low.
    """

    if balance < 0:
        st.error(
            f"⚠️ Account balance is negative: ₹{balance:,.2f}"
        )

    elif balance <= warning_threshold:
        st.warning(
            f"⚠️ Low balance: ₹{balance:,.2f}"
        )


def show_budget_alert(
    spent,
    budget,
) -> None:
    """
    Show budget usage alerts.
    """

    if budget <= 0:
        return

    usage_percentage = (spent / budget) * 100

    if usage_percentage >= 100:
        st.error(
            f"🚨 Budget exceeded: ₹{spent:,.2f} / ₹{budget:,.2f}"
        )

    elif usage_percentage >= 80:
        st.warning(
            f"⚠️ Budget is {usage_percentage:.0f}% used."
        )


def show_friend_money_alert(
    outstanding,
) -> None:
    """
    Show an alert when money belonging to friends is being held.
    """

    if outstanding > 0:
        st.warning(
            f"🤝 Friend money held: ₹{outstanding:,.2f}"
        )


def show_savings_progress_alert(
    contributed,
    target,
) -> None:
    """
    Display savings goal progress.
    """

    if target <= 0:
        return

    progress = min((contributed / target) * 100, 100)

    if progress >= 100:
        st.success(
            "🎉 Savings goal completed!"
        )

    elif progress >= 75:
        st.info(
            f"💎 Savings goal is {progress:.0f}% complete."
        )