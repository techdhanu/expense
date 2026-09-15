from decimal import Decimal

from utils.calculations import (
    calculate_account_balance,
    calculate_actual_money,
    calculate_friend_money_outstanding,
    calculate_savings_progress,
    calculate_total_balance,
)


def test_account_balance():
    balance = calculate_account_balance(
        opening_balance=Decimal("1000.00"),
        income=Decimal("5000.00"),
        expenses=Decimal("2000.00"),
        money_received=Decimal("500.00"),
        money_returned=Decimal("200.00"),
        transfers_in=Decimal("1000.00"),
        transfers_out=Decimal("500.00"),
        adjustments=Decimal("100.00"),
    )

    assert balance == Decimal("4900.00")


def test_total_balance():
    balances = [
        Decimal("1000.00"),
        Decimal("2500.00"),
        Decimal("-500.00"),
    ]

    assert calculate_total_balance(balances) == Decimal("3000.00")


def test_actual_money():
    total_balance = Decimal("10000.00")
    friend_money_held = Decimal("2500.00")

    assert calculate_actual_money(
        total_balance,
        friend_money_held,
    ) == Decimal("7500.00")


def test_friend_money_outstanding():
    received = Decimal("5000.00")
    returned = Decimal("2000.00")

    assert calculate_friend_money_outstanding(
        received,
        returned,
    ) == Decimal("3000.00")


def test_savings_progress():
    result = calculate_savings_progress(
        Decimal("3000.00"),
        Decimal("10000.00"),
    )

    assert result == Decimal("30.00")


def test_savings_goal_completed():
    result = calculate_savings_progress(
        Decimal("10000.00"),
        Decimal("10000.00"),
    )

    assert result == Decimal("100.00")