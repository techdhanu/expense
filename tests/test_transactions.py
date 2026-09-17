from decimal import Decimal
from datetime import date
from uuid import uuid4

import pytest

from services.account_service import (
    create_account,
    get_account_balance,
    deactivate_account,
)
from services.transaction_service import (
    create_expense,
    create_income,
    create_transaction,
    create_transfer,
    delete_transaction,
    update_transaction,
)
from database.queries import get_table


# =========================================================
# TEST ACCOUNT FIXTURE
# =========================================================

@pytest.fixture
def test_accounts():
    """
    Create two completely isolated test accounts.

    Every test receives fresh accounts with:
        - unique names
        - ₹0.00 opening balance
        - no dependency on real user accounts

    Accounts are deactivated after the test.
    """

    unique_id = uuid4().hex

    salary = create_account(
        name=f"PYTEST Salary {unique_id}",
        account_type="bank",
        opening_balance=Decimal("0.00"),
    )

    general = create_account(
        name=f"PYTEST General {unique_id}",
        account_type="bank",
        opening_balance=Decimal("0.00"),
    )

    try:
        yield salary, general

    finally:
        # -------------------------------------------------
        # Test accounts are never physically deleted.
        # They are deactivated to preserve account history.
        # -------------------------------------------------

        try:
            deactivate_account(salary["id"])
        except Exception:
            pass

        try:
            deactivate_account(general["id"])
        except Exception:
            pass


# =========================================================
# CREATE INCOME
# =========================================================

def test_create_income(test_accounts):

    salary, _ = test_accounts

    tx = create_income(
        date.today(),
        Decimal("5000.00"),
        salary["id"],
        description="PYTEST INCOME",
    )

    try:
        assert Decimal(
            str(tx["amount"])
        ) == Decimal("5000.00")

        balance = get_account_balance(
            salary["id"]
        )

        assert balance == Decimal("5000.00")

    finally:
        delete_transaction(tx["id"])


# =========================================================
# CREATE EXPENSE
# =========================================================

def test_create_expense(test_accounts):

    _, general = test_accounts

    tx = create_expense(
        date.today(),
        Decimal("1200.00"),
        general["id"],
        description="PYTEST EXPENSE",
    )

    try:
        assert Decimal(
            str(tx["amount"])
        ) == Decimal("1200.00")

        balance = get_account_balance(
            general["id"]
        )

        assert balance == Decimal("-1200.00")

    finally:
        delete_transaction(tx["id"])


# =========================================================
# TRANSFER
# =========================================================

def test_transfer_keeps_total_balance_unchanged(
    test_accounts,
):

    salary, general = test_accounts

    tx = create_transfer(
        date.today(),
        Decimal("2000.00"),
        salary["id"],
        general["id"],
        "PYTEST TRANSFER",
    )

    try:
        assert Decimal(
            str(tx["amount"])
        ) == Decimal("2000.00")

        salary_balance = get_account_balance(
            salary["id"]
        )

        general_balance = get_account_balance(
            general["id"]
        )

        # Source loses money.
        assert salary_balance == Decimal("-2000.00")

        # Destination receives money.
        assert general_balance == Decimal("2000.00")

        # Transfer has zero net effect.
        assert (
            salary_balance + general_balance
            == Decimal("0.00")
        )

    finally:
        delete_transaction(tx["id"])


# =========================================================
# TRANSFER EDIT
# =========================================================

def test_transfer_edit_updates_linked_transfer(
    test_accounts,
):

    salary, general = test_accounts

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
            {
                "amount": "3000.00",
            },
        )

        assert Decimal(
            str(updated["amount"])
        ) == Decimal("3000.00")

        # -------------------------------------------------
        # Verify linked transfer record
        # -------------------------------------------------

        linked = (
            get_table("transfers")
            .select("amount")
            .eq("transaction_id", tx["id"])
            .execute()
            .data
        )

        assert len(linked) == 1

        assert Decimal(
            str(linked[0]["amount"])
        ) == Decimal("3000.00")

        # -------------------------------------------------
        # Verify account balances
        # -------------------------------------------------

        salary_balance = get_account_balance(
            salary["id"]
        )

        general_balance = get_account_balance(
            general["id"]
        )

        assert salary_balance == Decimal("-3000.00")
        assert general_balance == Decimal("3000.00")

        # Transfer remains financially neutral.
        assert (
            salary_balance + general_balance
            == Decimal("0.00")
        )

    finally:
        delete_transaction(tx["id"])


# =========================================================
# INVALID TRANSACTION TYPE
# =========================================================

def test_invalid_transaction_type_is_rejected():

    with pytest.raises(
        ValueError,
        match="Invalid transaction type",
    ):
        create_transaction(
            transaction_date=date.today(),
            transaction_type="invalid_type",
            amount=100,
        )


# =========================================================
# ZERO AMOUNT
# =========================================================

def test_zero_amount_is_rejected():

    with pytest.raises(
        ValueError,
        match="greater than",
    ):
        create_transaction(
            transaction_date=date.today(),
            transaction_type="expense",
            amount=0,
            source_account_id="invalid-account-id",
        )