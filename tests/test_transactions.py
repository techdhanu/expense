from decimal import Decimal
from datetime import date

import pytest

from services.account_service import (
    get_all_accounts,
    get_account_balance,
    get_total_current_balance,
)
from services.transaction_service import (
    create_expense,
    create_income,
    create_transaction,
    create_transfer,
    delete_transaction,
    update_transaction,
)


def get_test_accounts():
    accounts = get_all_accounts()

    salary = next(
        a for a in accounts
        if a["name"] == "Salary Account"
    )

    general = next(
        a for a in accounts
        if a["name"] == "General Account"
    )

    return salary, general


def test_create_income():
    salary, _ = get_test_accounts()

    tx = create_income(
        date.today(),
        Decimal("5000.00"),
        salary["id"],
        description="PYTEST INCOME",
    )

    try:
        assert Decimal(str(tx["amount"])) == Decimal("5000.00")

        balance = get_account_balance(salary["id"])
        assert balance == Decimal("5000.00")
    finally:
        delete_transaction(tx["id"])


def test_create_expense():
    general, _ = get_test_accounts()

    tx = create_expense(
        date.today(),
        Decimal("1200.00"),
        general["id"],
        description="PYTEST EXPENSE",
    )

    try:
        assert Decimal(str(tx["amount"])) == Decimal("1200.00")

        balance = get_account_balance(general["id"])
        assert balance == Decimal("-1200.00")
    finally:
        delete_transaction(tx["id"])


def test_transfer_keeps_total_balance_unchanged():
    salary, general = get_test_accounts()

    tx = create_transfer(
        date.today(),
        Decimal("2000.00"),
        salary["id"],
        general["id"],
        "PYTEST TRANSFER",
    )

    try:
        assert Decimal(str(tx["amount"])) == Decimal("2000.00")

        salary_balance = get_account_balance(salary["id"])
        general_balance = get_account_balance(general["id"])
        total_balance = get_total_current_balance()

        assert salary_balance == Decimal("-2000.00")
        assert general_balance == Decimal("2000.00")
        assert total_balance == Decimal("0.00")
    finally:
        delete_transaction(tx["id"])


def test_transfer_edit_updates_linked_transfer():
    salary, general = get_test_accounts()

    tx = create_transfer(
        date.today(),
        Decimal("2000.00"),
        salary["id"],
        general["id"],
        "PYTEST TRANSFER EDIT",
    )

    try:
        updated = update_transaction(
            tx["id"],
            {"amount": "3000.00"},
        )

        assert Decimal(str(updated["amount"])) == Decimal("3000.00")

        from database.queries import get_table

        linked = (
            get_table("transfers")
            .select("amount")
            .eq("transaction_id", tx["id"])
            .execute()
            .data
        )

        assert len(linked) == 1
        assert Decimal(str(linked[0]["amount"])) == Decimal("3000.00")

        assert get_account_balance(salary["id"]) == Decimal("-3000.00")
        assert get_account_balance(general["id"]) == Decimal("3000.00")
        assert get_total_current_balance() == Decimal("0.00")
    finally:
        delete_transaction(tx["id"])


def test_invalid_transaction_type_is_rejected():
    with pytest.raises(ValueError, match="Invalid transaction type"):
        create_transaction(
            transaction_date=date.today(),
            transaction_type="invalid_type",
            amount=100,
        )


def test_zero_amount_is_rejected():
    with pytest.raises(ValueError, match="greater than"):
        create_transaction(
            transaction_date=date.today(),
            transaction_type="expense",
            amount=0,
            source_account_id="invalid-account-id",
        )