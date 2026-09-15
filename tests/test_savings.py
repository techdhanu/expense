from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.account_service import ensure_default_accounts, get_all_accounts
from services.savings_service import (
    create_savings_goal,
    contribute_to_savings_goal,
    get_goal_status,
    update_savings_goal,
)


def get_savings_test_account():
    ensure_default_accounts()

    accounts = get_all_accounts()

    return next(
        account
        for account in accounts
        if account["name"] == "Savings / Money Held Account"
    )


def test_create_savings_goal_and_contribution():
    account = get_savings_test_account()

    goal = create_savings_goal(
        name="PYTEST SAVINGS GOAL",
        target_amount=Decimal("10000.00"),
        target_date=date.today(),
        notes="Automated test",
    )

    try:
        assert Decimal(str(goal["target_amount"])) == Decimal("10000.00")

        contribution = contribute_to_savings_goal(
            goal_id=goal["id"],
            account_id=account["id"],
            amount=Decimal("3000.00"),
            contribution_date=date.today(),
            notes="PYTEST CONTRIBUTION",
        )

        assert Decimal(str(contribution["amount"])) == Decimal("3000.00")

        status = get_goal_status(goal["id"])

        assert Decimal(str(status["contributed"])) == Decimal("3000.00")
        assert Decimal(str(status["remaining"])) == Decimal("7000.00")
        assert Decimal(str(status["percentage"])) == Decimal("30.00")

    finally:
        # Delete contributions first because of foreign-key restrictions.
        contributions = (
            get_table("savings_contributions")
            .select("id, transaction_id")
            .eq("savings_goal_id", goal["id"])
            .execute()
            .data
        )

        for item in contributions:
            get_table("savings_contributions").delete().eq(
                "id", item["id"]
            ).execute()

            if item.get("transaction_id"):
                get_table("transactions").delete().eq(
                    "id", item["transaction_id"]
                ).execute()

        get_table("savings_goals").delete().eq(
            "id", goal["id"]
        ).execute()


def test_savings_goal_update():
    goal = create_savings_goal(
        name="PYTEST SAVINGS UPDATE",
        target_amount=Decimal("10000.00"),
        notes="Before update",
    )

    try:
        updated = update_savings_goal(
            goal["id"],
            {
                "target_amount": Decimal("20000.00"),
                "notes": "After update",
            },
        )

        assert Decimal(str(updated["target_amount"])) == Decimal("20000.00")
        assert updated["notes"] == "After update"

    finally:
        get_table("savings_goals").delete().eq(
            "id", goal["id"]
        ).execute()
