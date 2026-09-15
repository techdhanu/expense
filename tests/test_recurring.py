from datetime import date, timedelta
from decimal import Decimal

from database.queries import get_table
from services.account_service import ensure_default_accounts, get_all_accounts
from services.recurring_service import (
    create_recurring_transaction,
    get_due_recurring_transactions,
    get_all_recurring_transactions,
    update_recurring_transaction,
)


def get_test_account():
    ensure_default_accounts()

    accounts = get_all_accounts()

    return next(
        account
        for account in accounts
        if account["name"] == "General Account"
    )


def test_create_and_find_due_recurring_transaction():
    account = get_test_account()

    recurring = create_recurring_transaction(
        transaction_name="PYTEST RECURRING",
        transaction_type="expense",
        amount=Decimal("1000.00"),
        account_id=account["id"],
        frequency="monthly",
        start_date=date.today(),
        next_due_date=date.today(),
        auto_create=False,
        notes="Automated test",
    )

    try:
        assert recurring["transaction_name"] == "PYTEST RECURRING"
        assert Decimal(str(recurring["amount"])) == Decimal("1000.00")

        due = get_due_recurring_transactions(date.today())

        due_ids = [item["id"] for item in due]

        assert recurring["id"] in due_ids

    finally:
        get_table("recurring_transactions").delete().eq(
            "id", recurring["id"]
        ).execute()


def test_update_recurring_transaction():
    account = get_test_account()

    recurring = create_recurring_transaction(
        transaction_name="PYTEST RECURRING UPDATE",
        transaction_type="expense",
        amount=Decimal("1000.00"),
        account_id=account["id"],
        frequency="monthly",
        start_date=date.today(),
        next_due_date=date.today() + timedelta(days=5),
        auto_create=False,
    )

    try:
        updated = update_recurring_transaction(
            recurring["id"],
            {
                "amount": Decimal("1500.00"),
                "notes": "Updated test",
            },
        )

        assert Decimal(str(updated["amount"])) == Decimal("1500.00")
        assert updated["notes"] == "Updated test"

    finally:
        get_table("recurring_transactions").delete().eq(
            "id", recurring["id"]
        ).execute()