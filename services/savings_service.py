from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.transaction_service import create_transaction
from utils.validators import validate_amount


def _decimal(value) -> Decimal:
    """Convert a value safely to Decimal."""
    return Decimal(str(value or "0.00"))


def get_all_savings_goals(
    include_inactive: bool = True,
) -> list[dict]:
    """Return savings goals."""

    query = (
        get_table("savings_goals")
        .select("*")
        .order("created_at", desc=True)
    )

    if not include_inactive:
        query = query.eq("status", "active")

    response = query.execute()

    return response.data or []


def get_savings_goal(
    goal_id: str,
) -> dict | None:
    """Return a single savings goal."""

    response = (
        get_table("savings_goals")
        .select("*")
        .eq("id", goal_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_savings_goal(
    name: str,
    target_amount,
    target_date: date | None = None,
    notes: str | None = None,
) -> dict:
    """Create a new savings goal."""

    name = name.strip()

    if not name:
        raise ValueError("Savings goal name is required.")

    target_amount = validate_amount(target_amount)

    response = (
        get_table("savings_goals")
        .insert(
            {
                "name": name,
                "target_amount": str(target_amount),
                "target_date": (
                    target_date.isoformat()
                    if target_date
                    else None
                ),
                "status": "active",
                "notes": notes.strip() if notes else None,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Savings goal could not be created."
        )

    return response.data[0]


def get_goal_contributed_amount(
    goal_id: str,
) -> Decimal:
    """Return the total amount contributed to a savings goal."""

    response = (
        get_table("savings_contributions")
        .select("amount")
        .eq("savings_goal_id", goal_id)
        .execute()
    )

    total = Decimal("0.00")

    for contribution in response.data or []:
        total += _decimal(
            contribution["amount"]
        )

    return total.quantize(Decimal("0.01"))


def get_goal_status(
    goal_id: str,
) -> dict:
    """Return savings goal progress."""

    goal = get_savings_goal(goal_id)

    if goal is None:
        raise ValueError("Savings goal not found.")

    target = _decimal(
        goal["target_amount"]
    )

    contributed = get_goal_contributed_amount(
        goal_id
    )

    remaining = max(
        target - contributed,
        Decimal("0.00"),
    )

    if target > 0:
        percentage = (
            contributed / target
        ) * Decimal("100")
    else:
        percentage = Decimal("0.00")

    percentage = min(
        percentage,
        Decimal("100.00"),
    )

    return {
        "goal_id": goal_id,
        "name": goal["name"],
        "target_amount": target.quantize(
            Decimal("0.01")
        ),
        "contributed": contributed,
        "remaining": remaining.quantize(
            Decimal("0.01")
        ),
        "percentage": percentage.quantize(
            Decimal("0.01")
        ),
        "status": goal["status"],
    }


def contribute_to_savings_goal(
    goal_id: str,
    account_id: str,
    amount,
    contribution_date: date,
    notes: str | None = None,
) -> dict:
    """
    Add money to a savings goal.

    The contribution is recorded as a transaction so the
    source account balance decreases accordingly.
    """

    amount = validate_amount(amount)

    goal = get_savings_goal(goal_id)

    if goal is None:
        raise ValueError("Savings goal not found.")

    if goal["status"] != "active":
        raise ValueError(
            "Only active savings goals can receive contributions."
        )

    transaction = create_transaction(
        transaction_date=contribution_date,
        transaction_type="savings_goal_contribution",
        amount=amount,
        source_account_id=account_id,
        description=f"Savings contribution: {goal['name']}",
        notes=notes,
    )

    response = (
        get_table("savings_contributions")
        .insert(
            {
                "savings_goal_id": goal_id,
                "transaction_id": transaction["id"],
                "account_id": account_id,
                "amount": str(amount),
                "contribution_date": contribution_date.isoformat(),
                "notes": notes.strip() if notes else None,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Savings contribution could not be created."
        )

    # Automatically mark the goal as completed when target is reached.
    status = get_goal_status(goal_id)

    if status["remaining"] <= Decimal("0.00"):
        (
            get_table("savings_goals")
            .update({"status": "completed"})
            .eq("id", goal_id)
            .execute()
        )

    return response.data[0]


def update_savings_goal(
    goal_id: str,
    updates: dict,
) -> dict:
    """Update a savings goal."""

    if not updates:
        raise ValueError("No changes were provided.")

    if "name" in updates:
        updates["name"] = str(
            updates["name"]
        ).strip()

        if not updates["name"]:
            raise ValueError(
                "Savings goal name cannot be empty."
            )

    if "target_amount" in updates:
        updates["target_amount"] = str(
            validate_amount(
                updates["target_amount"]
            )
        )

    if "target_date" in updates:
        target_date = updates["target_date"]

        updates["target_date"] = (
            target_date.isoformat()
            if target_date
            else None
        )

    response = (
        get_table("savings_goals")
        .update(updates)
        .eq("id", goal_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Savings goal could not be updated."
        )

    return response.data[0]


def cancel_savings_goal(
    goal_id: str,
) -> dict:
    """Cancel a savings goal without deleting its history."""

    goal = get_savings_goal(goal_id)

    if goal is None:
        raise ValueError("Savings goal not found.")

    response = (
        get_table("savings_goals")
        .update({"status": "cancelled"})
        .eq("id", goal_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Savings goal could not be cancelled."
        )

    return response.data[0]