from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.authentication_service import get_current_user_id
from services.transaction_service import create_transaction
from utils.validators import validate_amount


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _decimal(value) -> Decimal:
    """Convert a value safely to Decimal."""
    return Decimal(str(value or "0.00"))


def _get_owned_goal(
    goal_id: str,
) -> dict:
    """
    Return a savings goal belonging to the current user.
    """

    if not goal_id:
        raise ValueError("Savings goal ID is required.")

    user_id = get_current_user_id()

    response = (
        get_table("savings_goals")
        .select("*")
        .eq("id", goal_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Savings goal not found or does not belong to the current user."
        )

    return response.data[0]


def _validate_owned_account(
    account_id: str,
) -> dict:
    """
    Return an active account belonging to the current user.
    """

    if not account_id:
        raise ValueError("Account ID is required.")

    user_id = get_current_user_id()

    response = (
        get_table("accounts")
        .select("*")
        .eq("id", account_id)
        .eq("user_id", user_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Account not found or does not belong to the current user."
        )

    return response.data[0]


# ============================================================
# SAVINGS GOALS
# ============================================================

def get_all_savings_goals(
    include_inactive: bool = True,
) -> list[dict]:
    """
    Return savings goals belonging to the current user.
    """

    user_id = get_current_user_id()

    query = (
        get_table("savings_goals")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )

    if not include_inactive:
        query = query.eq(
            "status",
            "active",
        )

    response = query.execute()

    return response.data or []


def get_savings_goal(
    goal_id: str,
) -> dict | None:
    """
    Return a single savings goal belonging to the
    current user.
    """

    if not goal_id:
        raise ValueError(
            "Savings goal ID is required."
        )

    user_id = get_current_user_id()

    response = (
        get_table("savings_goals")
        .select("*")
        .eq("id", goal_id)
        .eq("user_id", user_id)
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
    """Create a new savings goal for the current user."""

    user_id = get_current_user_id()

    if not name:
        raise ValueError(
            "Savings goal name is required."
        )

    name = name.strip()

    if not name:
        raise ValueError(
            "Savings goal name is required."
        )

    target_amount = validate_amount(
        target_amount
    )

    response = (
        get_table("savings_goals")
        .insert(
            {
                "user_id": user_id,
                "name": name,
                "target_amount": str(target_amount),
                "target_date": (
                    target_date.isoformat()
                    if target_date
                    else None
                ),
                "status": "active",
                "notes": (
                    notes.strip()
                    if notes
                    else None
                ),
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Savings goal could not be created."
        )

    return response.data[0]


# ============================================================
# SAVINGS CONTRIBUTIONS
# ============================================================

def get_goal_contributed_amount(
    goal_id: str,
) -> Decimal:
    """
    Return the total amount contributed to a savings goal.

    Only contributions belonging to the current user
    are included.
    """

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Verify goal ownership first
    # --------------------------------------------------------
    _get_owned_goal(goal_id)

    response = (
        get_table("savings_contributions")
        .select("amount")
        .eq("savings_goal_id", goal_id)
        .eq("user_id", user_id)
        .execute()
    )

    total = Decimal("0.00")

    for contribution in response.data or []:
        total += _decimal(
            contribution["amount"]
        )

    return total.quantize(
        Decimal("0.01")
    )


def get_goal_status(
    goal_id: str,
) -> dict:
    """Return savings goal progress for the current user."""

    goal = _get_owned_goal(goal_id)

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


# ============================================================
# CONTRIBUTE TO SAVINGS GOAL
# ============================================================

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

    user_id = get_current_user_id()

    amount = validate_amount(
        amount
    )

    # --------------------------------------------------------
    # Verify goal belongs to current user
    # --------------------------------------------------------
    goal = _get_owned_goal(goal_id)

    if goal["status"] != "active":
        raise ValueError(
            "Only active savings goals can receive contributions."
        )

    # --------------------------------------------------------
    # Verify account belongs to current user
    # --------------------------------------------------------
    _validate_owned_account(
        account_id
    )

    # --------------------------------------------------------
    # Create transaction
    #
    # transaction_service also validates ownership.
    # --------------------------------------------------------
    transaction = create_transaction(
        transaction_date=contribution_date,
        transaction_type="savings_goal_contribution",
        amount=amount,
        source_account_id=account_id,
        description=f"Savings contribution: {goal['name']}",
        notes=notes,
    )

    # --------------------------------------------------------
    # Create contribution record
    # --------------------------------------------------------
    response = (
        get_table("savings_contributions")
        .insert(
            {
                "user_id": user_id,
                "savings_goal_id": goal_id,
                "transaction_id": transaction["id"],
                "account_id": account_id,
                "amount": str(amount),
                "contribution_date": (
                    contribution_date.isoformat()
                ),
                "notes": (
                    notes.strip()
                    if notes
                    else None
                ),
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Savings contribution could not be created."
        )

    # --------------------------------------------------------
    # Automatically mark the goal completed when target
    # is reached.
    # --------------------------------------------------------
    status = get_goal_status(
        goal_id
    )

    if status["remaining"] <= Decimal("0.00"):

        (
            get_table("savings_goals")
            .update(
                {
                    "status": "completed"
                }
            )
            .eq(
                "id",
                goal_id,
            )
            .eq(
                "user_id",
                user_id,
            )
            .execute()
        )

    return response.data[0]


# ============================================================
# UPDATE SAVINGS GOAL
# ============================================================

def update_savings_goal(
    goal_id: str,
    updates: dict,
) -> dict:
    """
    Update a savings goal belonging to the current user.
    """

    if not updates:
        raise ValueError(
            "No changes were provided."
        )

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Verify ownership
    # --------------------------------------------------------
    _get_owned_goal(goal_id)

    # --------------------------------------------------------
    # Only allow supported fields
    # --------------------------------------------------------
    allowed_fields = {
        "name",
        "target_amount",
        "target_date",
        "notes",
    }

    unexpected_fields = (
        set(updates) - allowed_fields
    )

    if unexpected_fields:
        raise ValueError(
            "Unsupported savings goal field(s): "
            + ", ".join(sorted(unexpected_fields))
        )

    clean_updates = {}

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------
    if "name" in updates:

        name = str(
            updates["name"]
        ).strip()

        if not name:
            raise ValueError(
                "Savings goal name cannot be empty."
            )

        clean_updates["name"] = name

    # --------------------------------------------------------
    # Target amount
    # --------------------------------------------------------
    if "target_amount" in updates:

        clean_updates["target_amount"] = str(
            validate_amount(
                updates["target_amount"]
            )
        )

    # --------------------------------------------------------
    # Target date
    # --------------------------------------------------------
    if "target_date" in updates:

        target_date = updates[
            "target_date"
        ]

        if target_date is not None and not isinstance(
            target_date,
            date,
        ):
            raise ValueError(
                "Invalid target date."
            )

        clean_updates["target_date"] = (
            target_date.isoformat()
            if target_date
            else None
        )

    # --------------------------------------------------------
    # Notes
    # --------------------------------------------------------
    if "notes" in updates:

        clean_updates["notes"] = (
            str(updates["notes"]).strip()
            if updates["notes"]
            else None
        )

    if not clean_updates:
        raise ValueError(
            "No valid changes were provided."
        )

    # --------------------------------------------------------
    # Update ONLY current user's goal
    # --------------------------------------------------------
    response = (
        get_table("savings_goals")
        .update(clean_updates)
        .eq("id", goal_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Savings goal could not be updated."
        )

    return response.data[0]


# ============================================================
# CANCEL SAVINGS GOAL
# ============================================================

def cancel_savings_goal(
    goal_id: str,
) -> dict:
    """
    Cancel a savings goal without deleting its history.
    """

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Verify ownership
    # --------------------------------------------------------
    goal = _get_owned_goal(
        goal_id
    )

    if goal["status"] == "cancelled":
        return goal

    response = (
        get_table("savings_goals")
        .update(
            {
                "status": "cancelled"
            }
        )
        .eq(
            "id",
            goal_id,
        )
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Savings goal could not be cancelled."
        )

    return response.data[0]