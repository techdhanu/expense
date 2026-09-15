from datetime import date
from decimal import Decimal

from database.queries import get_table
from utils.constants import RECURRING_FREQUENCIES
from utils.validators import validate_amount


def get_all_recurring_transactions(
    active_only: bool = False,
) -> list[dict]:
    """Return recurring transaction definitions."""

    query = (
        get_table("recurring_transactions")
        .select("*")
        .order("next_due_date")
    )

    if active_only:
        query = query.eq("is_active", True)

    response = query.execute()

    return response.data or []


def get_recurring_transaction(
    recurring_id: str,
) -> dict | None:
    """Return one recurring transaction."""

    response = (
        get_table("recurring_transactions")
        .select("*")
        .eq("id", recurring_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_recurring_transaction(
    transaction_name: str,
    transaction_type: str,
    amount,
    account_id: str,
    frequency: str,
    start_date: date,
    next_due_date: date,
    destination_account_id: str | None = None,
    category_id: str | None = None,
    payment_method: str | None = None,
    auto_create: bool = False,
    notes: str | None = None,
) -> dict:
    """Create a recurring transaction definition."""

    transaction_name = transaction_name.strip()

    if not transaction_name:
        raise ValueError(
            "Transaction name is required."
        )

    if transaction_type not in {
        "income",
        "expense",
        "internal_transfer",
    }:
        raise ValueError(
            "Invalid recurring transaction type."
        )

    if frequency not in RECURRING_FREQUENCIES:
        raise ValueError(
            "Invalid recurring frequency."
        )

    amount = validate_amount(amount)

    if not account_id:
        raise ValueError("Account is required.")

    if transaction_type == "internal_transfer":
        if not destination_account_id:
            raise ValueError(
                "Transfer requires a destination account."
            )

        if account_id == destination_account_id:
            raise ValueError(
                "Source and destination accounts must be different."
            )

    response = (
        get_table("recurring_transactions")
        .insert(
            {
                "transaction_name": transaction_name,
                "transaction_type": transaction_type,
                "amount": str(amount),
                "account_id": account_id,
                "destination_account_id": destination_account_id,
                "category_id": category_id,
                "payment_method": payment_method,
                "frequency": frequency,
                "start_date": start_date.isoformat(),
                "next_due_date": next_due_date.isoformat(),
                "is_active": True,
                "auto_create": auto_create,
                "notes": notes.strip() if notes else None,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Recurring transaction could not be created."
        )

    return response.data[0]


def update_recurring_transaction(
    recurring_id: str,
    updates: dict,
) -> dict:
    """Update a recurring transaction."""

    if not updates:
        raise ValueError(
            "No changes were provided."
        )

    if "amount" in updates:
        updates["amount"] = str(
            validate_amount(updates["amount"])
        )

    if "transaction_name" in updates:
        updates["transaction_name"] = str(
            updates["transaction_name"]
        ).strip()

        if not updates["transaction_name"]:
            raise ValueError(
                "Transaction name cannot be empty."
            )

    if "frequency" in updates:
        if updates["frequency"] not in RECURRING_FREQUENCIES:
            raise ValueError(
                "Invalid recurring frequency."
            )

    for field in [
        "start_date",
        "next_due_date",
    ]:
        if field in updates and updates[field]:
            updates[field] = updates[field].isoformat()

    response = (
        get_table("recurring_transactions")
        .update(updates)
        .eq("id", recurring_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Recurring transaction could not be updated."
        )

    return response.data[0]


def deactivate_recurring_transaction(
    recurring_id: str,
) -> dict:
    """Deactivate a recurring transaction."""

    recurring = get_recurring_transaction(
        recurring_id
    )

    if recurring is None:
        raise ValueError(
            "Recurring transaction not found."
        )

    response = (
        get_table("recurring_transactions")
        .update({"is_active": False})
        .eq("id", recurring_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Recurring transaction could not be deactivated."
        )

    return response.data[0]


def activate_recurring_transaction(
    recurring_id: str,
) -> dict:
    """Activate a recurring transaction."""

    recurring = get_recurring_transaction(
        recurring_id
    )

    if recurring is None:
        raise ValueError(
            "Recurring transaction not found."
        )

    response = (
        get_table("recurring_transactions")
        .update({"is_active": True})
        .eq("id", recurring_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Recurring transaction could not be activated."
        )

    return response.data[0]


def get_due_recurring_transactions(
    as_of_date: date | None = None,
) -> list[dict]:
    """
    Return active recurring transactions whose next due date
    is today or earlier.
    """

    as_of_date = as_of_date or date.today()

    response = (
        get_table("recurring_transactions")
        .select("*")
        .eq("is_active", True)
        .lte("next_due_date", as_of_date.isoformat())
        .order("next_due_date")
        .execute()
    )

    return response.data or []