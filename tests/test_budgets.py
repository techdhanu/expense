from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.account_service import create_account
from services.budget_service import (
    create_budget,
    get_budget_status,
    update_budget,
)
from services.category_service import create_category
from services.transaction_service import create_expense, delete_transaction


def create_test_category():
    category = create_category(
        name="PYTEST FOOD",
        category_type="expense",
    )

    return category


def create_test_account():
    account = create_account(
        name="PYTEST GENERAL ACCOUNT",
        account_type="bank",
        opening_balance=Decimal("10000.00"),
    )

    return account


def test_create_and_update_budget():
    category = create_test_category()

    budget = create_budget(
        category_id=category["id"],
        month=date.today().month,
        year=date.today().year,
        amount=Decimal("5000.00"),
    )

    try:
        assert Decimal(str(budget["budget_amount"])) == Decimal("5000.00")

        updated = update_budget(
            budget["id"],
            Decimal("6000.00"),
        )

        assert Decimal(str(updated["budget_amount"])) == Decimal("6000.00")

    finally:
        get_table("budgets").delete().eq(
            "id", budget["id"]
        ).execute()

        get_table("categories").delete().eq(
            "id", category["id"]
        ).execute()


def test_budget_status_with_expense():
    category = create_test_category()
    account = create_test_account()

    budget = create_budget(
        category_id=category["id"],
        month=date.today().month,
        year=date.today().year,
        amount=Decimal("5000.00"),
    )

    transaction = create_expense(
        transaction_date=date.today(),
        amount=Decimal("1500.00"),
        account_id=account["id"],
        category_id=category["id"],
        description="PYTEST BUDGET EXPENSE",
    )

    try:
        status = get_budget_status(
            budget,
            Decimal("1500.00"),
        )

        assert Decimal(str(status["budget_amount"])) == Decimal("5000.00")
        assert Decimal(str(status["spent"])) == Decimal("1500.00")
        assert Decimal(str(status["remaining"])) == Decimal("3500.00")

    finally:
        delete_transaction(transaction["id"])

        get_table("budgets").delete().eq(
            "id", budget["id"]
        ).execute()

        get_table("categories").delete().eq(
            "id", category["id"]
        ).execute()

        get_table("accounts").delete().eq(
            "id", account["id"]
        ).execute()