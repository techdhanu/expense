from datetime import date
from decimal import Decimal

import pytest

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


def cleanup_savings_goal(goal_id):
    """
    Remove all records created for a savings-goal test.

    Contributions must be deleted before their linked
    transactions/goals because of foreign-key constraints.
    """

    contributions = (
        get_table("savings_contributions")
        .select("id, transaction_id")
        .eq("savings_goal_id", goal_id)
        .execute()
        .data
        or []
    )

    transaction_ids = [
        item["transaction_id"]
        for item in contributions
        if item.get("transaction_id")
    ]

    for item in contributions:
        (
            get_table("savings_contributions")
            .delete()
            .eq("id", item["id"])
            .eq("savings_goal_id", goal_id)
            .execute()
        )

    for transaction_id in transaction_ids:
        (
            get_table("transactions")
            .delete()
            .eq("id", transaction_id)
            .execute()
        )

    (
        get_table("savings_goals")
        .delete()
        .eq("id", goal_id)
        .execute()
    )


def test_create_savings_goal_and_atomic_contribution():
    account = get_savings_test_account()

    goal = create_savings_goal(
        name="PYTEST SAVINGS GOAL",
        target_amount=Decimal("10000.00"),
        target_date=date.today(),
        notes="Automated test",
    )

    try:
        # ----------------------------------------------------
        # Goal creation
        # ----------------------------------------------------
        assert goal["name"] == "PYTEST SAVINGS GOAL"
        assert Decimal(
            str(goal["target_amount"])
        ) == Decimal("10000.00")

        # ----------------------------------------------------
        # Atomic contribution
        # ----------------------------------------------------
        contribution = contribute_to_savings_goal(
            goal_id=goal["id"],
            account_id=account["id"],
            amount=Decimal("3000.00"),
            contribution_date=date.today(),
            notes="PYTEST CONTRIBUTION",
        )

        assert contribution["user_id"]
        assert contribution["savings_goal_id"] == goal["id"]
        assert contribution["account_id"] == account["id"]
        assert contribution["transaction_id"]

        assert Decimal(
            str(contribution["amount"])
        ) == Decimal("3000.00")

        # ----------------------------------------------------
        # Verify the linked transaction exists
        # ----------------------------------------------------
        transaction = (
            get_table("transactions")
            .select("*")
            .eq(
                "id",
                contribution["transaction_id"],
            )
            .eq(
                "user_id",
                contribution["user_id"],
            )
            .limit(1)
            .execute()
            .data
        )

        assert len(transaction) == 1

        transaction = transaction[0]

        assert transaction["transaction_type"] == (
            "savings_goal_contribution"
        )

        assert transaction["source_account_id"] == account["id"]
        assert transaction["destination_account_id"] is None

        assert Decimal(
            str(transaction["amount"])
        ) == Decimal("3000.00")

        assert transaction["description"] == (
            "Savings contribution: PYTEST SAVINGS GOAL"
        )

        assert transaction["notes"] == "PYTEST CONTRIBUTION"

        # ----------------------------------------------------
        # Verify contribution record points to transaction
        # ----------------------------------------------------
        contribution_record = (
            get_table("savings_contributions")
            .select("*")
            .eq(
                "id",
                contribution["id"],
            )
            .eq(
                "user_id",
                contribution["user_id"],
            )
            .limit(1)
            .execute()
            .data
        )

        assert len(contribution_record) == 1

        contribution_record = contribution_record[0]

        assert contribution_record["transaction_id"] == (
            transaction["id"]
        )

        assert contribution_record["savings_goal_id"] == (
            goal["id"]
        )

        assert contribution_record["account_id"] == (
            account["id"]
        )

        assert Decimal(
            str(contribution_record["amount"])
        ) == Decimal("3000.00")

        # ----------------------------------------------------
        # Verify goal calculations
        # ----------------------------------------------------
        status = get_goal_status(goal["id"])

        assert Decimal(
            str(status["contributed"])
        ) == Decimal("3000.00")

        assert Decimal(
            str(status["remaining"])
        ) == Decimal("7000.00")

        assert Decimal(
            str(status["percentage"])
        ) == Decimal("30.00")

        assert status["status"] == "active"

    finally:
        cleanup_savings_goal(goal["id"])


def test_savings_goal_completion():
    account = get_savings_test_account()

    goal = create_savings_goal(
        name="PYTEST SAVINGS COMPLETE",
        target_amount=Decimal("5000.00"),
        notes="Completion test",
    )

    try:
        contribution = contribute_to_savings_goal(
            goal_id=goal["id"],
            account_id=account["id"],
            amount=Decimal("5000.00"),
            contribution_date=date.today(),
            notes="Complete goal",
        )

        assert Decimal(
            str(contribution["amount"])
        ) == Decimal("5000.00")

        assert contribution["goal_status"] == "completed"

        assert Decimal(
            str(contribution["total_contributed"])
        ) == Decimal("5000.00")

        status = get_goal_status(goal["id"])

        assert Decimal(
            str(status["contributed"])
        ) == Decimal("5000.00")

        assert Decimal(
            str(status["remaining"])
        ) == Decimal("0.00")

        assert Decimal(
            str(status["percentage"])
        ) == Decimal("100.00")

        assert status["status"] == "completed"

    finally:
        cleanup_savings_goal(goal["id"])


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

        assert Decimal(
            str(updated["target_amount"])
        ) == Decimal("20000.00")

        assert updated["notes"] == "After update"

    finally:
        cleanup_savings_goal(goal["id"])


def test_savings_goal_rejects_unsupported_update_field():
    goal = create_savings_goal(
        name="PYTEST SAVINGS VALIDATION",
        target_amount=Decimal("10000.00"),
    )

    try:
        with pytest.raises(ValueError):
            update_savings_goal(
                goal["id"],
                {
                    "user_id": "should-not-be-changeable",
                },
            )

    finally:
        cleanup_savings_goal(goal["id"])