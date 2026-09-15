from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.budget_service import (
    create_budget,
    get_budget_status,
    update_budget,
)
from services.category_service import get_categories_by_type
from services.transaction_service import create_expense, delete_transaction


def get_test_category():
    categories = get_categories_by_type("expense")

    return next(
        category
        for category in categories
        if category["name"] == "Food"
    )


def test_create_and_update_budget():
    category = get_test_category()

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


def test_budget_status_with_expense():
    category = get_test_category()

    budget = create_budget(
        category_id=category["id"],
        month=date.today().month,
        year=date.today().year,
        amount=Decimal("5000.00"),
    )

    account_response = (
        get_table("accounts")
        .select("id")
        .eq("name", "General Account")
        .limit(1)
        .execute()
    )

    account_id = account_response.data[0]["id"]

    transaction = create_expense(
        transaction_date=date.today(),
        amount=Decimal("1500.00"),
        account_id=account_id,
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