from decimal import Decimal
from typing import Iterable


def decimal_sum(values: Iterable) -> Decimal:
    """Safely sum monetary values using Decimal."""
    total = Decimal("0.00")

    for value in values:
        total += Decimal(str(value))

    return total


def calculate_account_balance(
    opening_balance,
    income,
    expenses,
    money_received,
    money_returned,
    transfers_in,
    transfers_out,
    adjustments,
) -> Decimal:
    """
    Calculate the current balance of an account.

    Transfers are internal movements and therefore do not change
    the combined balance across all accounts.
    """

    balance = Decimal(str(opening_balance))

    balance += Decimal(str(income))
    balance -= Decimal(str(expenses))
    balance += Decimal(str(money_received))
    balance -= Decimal(str(money_returned))
    balance += Decimal(str(transfers_in))
    balance -= Decimal(str(transfers_out))
    balance += Decimal(str(adjustments))

    return balance.quantize(Decimal("0.01"))


def calculate_total_balance(account_balances: Iterable) -> Decimal:
    """Calculate total money across all accounts."""
    return decimal_sum(account_balances).quantize(Decimal("0.01"))


def calculate_actual_money(
    total_balance,
    friend_money_held,
) -> Decimal:
    """
    Calculate actual personal money.

    Friend money is a liability, so it is excluded from
    the user's own available money.
    """
    actual_money = (
        Decimal(str(total_balance))
        - Decimal(str(friend_money_held))
    )

    return actual_money.quantize(Decimal("0.01"))


def calculate_friend_money_outstanding(
    amount_received,
    amount_returned,
) -> Decimal:
    """Calculate money still owed to a friend."""
    outstanding = (
        Decimal(str(amount_received))
        - Decimal(str(amount_returned))
    )

    return outstanding.quantize(Decimal("0.01"))


def calculate_savings_progress(
    contributed_amount,
    target_amount,
) -> Decimal:
    """Calculate savings goal completion percentage."""
    target = Decimal(str(target_amount))

    if target <= 0:
        return Decimal("0.00")

    progress = (
        Decimal(str(contributed_amount)) / target
    ) * Decimal("100")

    if progress > 100:
        progress = Decimal("100")

    return progress.quantize(Decimal("0.01"))