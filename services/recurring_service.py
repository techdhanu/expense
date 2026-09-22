from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.authentication_service import get_current_user_id
from services.account_service import get_account
from utils.constants import RECURRING_FREQUENCIES
from utils.validators import validate_amount


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_owned_recurring(recurring_id: str) -> dict | None:
    """Return a recurring transaction owned by the current user."""

    user_id = get_current_user_id()

    response = (
        get_table("recurring_transactions")
        .select("*")
        .eq("id", recurring_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def _validate_owned_account(account_id: str) -> None:
    """Ensure the account belongs to the current user."""

    if not account_id:
        raise ValueError("Account is required.")

    account = get_account(account_id)

    if account is None:
        raise ValueError(
            "Selected account does not belong to the current user."
        )


def _validate_owned_category(category_id: str | None) -> None:
    """Ensure the category belongs to the current user."""

    if not category_id:
        return

    user_id = get_current_user_id()

    response = (
        get_table("categories")
        .select("id")
        .eq("id", category_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Selected category does not belong to the current user."
        )


# ============================================================
# READ OPERATIONS
# ============================================================

def get_all_recurring_transactions(
    active_only: bool = False,
) -> list[dict]:
    """Return recurring transaction definitions for the current user."""

    user_id = get_current_user_id()

    query = (
        get_table("recurring_transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("next_due_date")
    )

    if active_only:
        query = query.eq("is_active", True)

    response = query.execute()

    return response.data or []


def get_recurring_transaction(
    recurring_id: str,
) -> dict | None:
    """Return one recurring transaction owned by the current user."""

    return _get_owned_recurring(recurring_id)


# ============================================================
# CREATE RECURRING TRANSACTION
# ============================================================

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

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    transaction_name = transaction_name.strip()

    if not transaction_name:
        raise ValueError("Transaction name is required.")

    if transaction_type not in {
        "income",
        "expense",
        "internal_transfer",
    }:
        raise ValueError("Invalid recurring transaction type.")

    if frequency not in RECURRING_FREQUENCIES:
        raise ValueError("Invalid recurring frequency.")

    amount = validate_amount(amount)

    # --------------------------------------------------------
    # Ownership validation
    # --------------------------------------------------------

    _validate_owned_account(account_id)
    _validate_owned_category(category_id)

    # --------------------------------------------------------
    # Transfer validation
    # --------------------------------------------------------

    if transaction_type == "internal_transfer":
        if not destination_account_id:
            raise ValueError(
                "Transfer requires a destination account."
            )

        if account_id == destination_account_id:
            raise ValueError(
                "Source and destination accounts must be different."
            )

        _validate_owned_account(destination_account_id)

    else:
        # Income and expense transactions must never
        # retain a destination account.
        destination_account_id = None

    # --------------------------------------------------------
    # Create recurring definition
    # --------------------------------------------------------

    response = (
        get_table("recurring_transactions")
        .insert(
            {
                "user_id": user_id,
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


# ============================================================
# UPDATE RECURRING TRANSACTION
# ============================================================

def update_recurring_transaction(
    recurring_id: str,
    updates: dict,
) -> dict:
    """
    Update a recurring transaction owned by the current user.

    The final transaction definition is always validated for
    consistency before being saved.
    """

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Ownership validation
    # --------------------------------------------------------

    recurring = _get_owned_recurring(recurring_id)

    if recurring is None:
        raise ValueError(
            "Recurring transaction not found."
        )

    if not updates:
        raise ValueError("No changes were provided.")

    # Never mutate the caller's dictionary.
    updates = dict(updates)

    # --------------------------------------------------------
    # Allowed fields
    # --------------------------------------------------------

    allowed_fields = {
        "transaction_name",
        "transaction_type",
        "amount",
        "account_id",
        "destination_account_id",
        "category_id",
        "payment_method",
        "frequency",
        "start_date",
        "next_due_date",
        "is_active",
        "auto_create",
        "notes",
    }

    unexpected_fields = (
        set(updates) - allowed_fields
    )

    if unexpected_fields:
        raise ValueError(
            "Unsupported recurring transaction field(s): "
            + ", ".join(sorted(unexpected_fields))
        )

    updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    if not updates:
        raise ValueError(
            "No valid changes were provided."
        )

    # --------------------------------------------------------
    # Validate transaction name
    # --------------------------------------------------------

    if "transaction_name" in updates:
        updates["transaction_name"] = str(
            updates["transaction_name"]
        ).strip()

        if not updates["transaction_name"]:
            raise ValueError(
                "Transaction name cannot be empty."
            )

    # --------------------------------------------------------
    # Validate transaction type
    # --------------------------------------------------------

    if "transaction_type" in updates:
        if updates["transaction_type"] not in {
            "income",
            "expense",
            "internal_transfer",
        }:
            raise ValueError(
                "Invalid recurring transaction type."
            )

    # --------------------------------------------------------
    # Validate amount
    # --------------------------------------------------------

    if "amount" in updates:
        updates["amount"] = str(
            validate_amount(
                updates["amount"]
            )
        )

    # --------------------------------------------------------
    # Validate frequency
    # --------------------------------------------------------

    if "frequency" in updates:
        if updates["frequency"] not in RECURRING_FREQUENCIES:
            raise ValueError(
                "Invalid recurring frequency."
            )

    # --------------------------------------------------------
    # Validate source account
    # --------------------------------------------------------

    if "account_id" in updates:
        _validate_owned_account(
            updates["account_id"]
        )

    # --------------------------------------------------------
    # Validate destination account
    # --------------------------------------------------------

    if "destination_account_id" in updates:
        destination_id = updates[
            "destination_account_id"
        ]

        if destination_id:
            _validate_owned_account(
                destination_id
            )

    # --------------------------------------------------------
    # Validate category
    # --------------------------------------------------------

    if "category_id" in updates:
        _validate_owned_category(
            updates["category_id"]
        )

    # --------------------------------------------------------
    # Determine FINAL transaction configuration
    #
    # We must validate the resulting record, not just the
    # individual fields supplied by the caller.
    # --------------------------------------------------------

    transaction_type = updates.get(
        "transaction_type",
        recurring["transaction_type"],
    )

    account_id = updates.get(
        "account_id",
        recurring["account_id"],
    )

    destination_account_id = updates.get(
        "destination_account_id",
        recurring.get("destination_account_id"),
    )

    # --------------------------------------------------------
    # Final transfer consistency validation
    # --------------------------------------------------------

    if transaction_type == "internal_transfer":

        if not destination_account_id:
            raise ValueError(
                "Transfer requires a destination account."
            )

        if account_id == destination_account_id:
            raise ValueError(
                "Source and destination accounts must be different."
            )

        # Validate the FINAL destination account as well.
        _validate_owned_account(
            destination_account_id
        )

    else:
        # CRITICAL FIX:
        #
        # Income and expense transactions must NEVER retain
        # a destination account, even when the caller only
        # changes transaction_type and does not explicitly
        # provide destination_account_id.
        updates["destination_account_id"] = None

    # --------------------------------------------------------
    # Date conversion
    # --------------------------------------------------------

    for field in [
        "start_date",
        "next_due_date",
    ]:
        if field in updates and updates[field]:

            if isinstance(updates[field], date):
                updates[field] = updates[field].isoformat()

    # --------------------------------------------------------
    # Notes
    # --------------------------------------------------------

    if "notes" in updates:
        updates["notes"] = (
            str(updates["notes"]).strip()
            if updates["notes"]
            else None
        )

    # --------------------------------------------------------
    # Final ownership-protected update
    # --------------------------------------------------------

    response = (
        get_table("recurring_transactions")
        .update(updates)
        .eq("id", recurring_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Recurring transaction could not be updated."
        )

    return response.data[0]


# ============================================================
# DEACTIVATE RECURRING TRANSACTION
# ============================================================

def deactivate_recurring_transaction(
    recurring_id: str,
) -> dict:
    """Deactivate a recurring transaction."""

    user_id = get_current_user_id()

    recurring = _get_owned_recurring(recurring_id)

    if recurring is None:
        raise ValueError(
            "Recurring transaction not found."
        )

    response = (
        get_table("recurring_transactions")
        .update(
            {
                "is_active": False,
            }
        )
        .eq("id", recurring_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Recurring transaction could not be deactivated."
        )

    return response.data[0]


# ============================================================
# ACTIVATE RECURRING TRANSACTION
# ============================================================

def activate_recurring_transaction(
    recurring_id: str,
) -> dict:
    """Activate a recurring transaction."""

    user_id = get_current_user_id()

    recurring = _get_owned_recurring(recurring_id)

    if recurring is None:
        raise ValueError(
            "Recurring transaction not found."
        )

    response = (
        get_table("recurring_transactions")
        .update(
            {
                "is_active": True,
            }
        )
        .eq("id", recurring_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Recurring transaction could not be activated."
        )

    return response.data[0]


# ============================================================
# DUE RECURRING TRANSACTIONS
# ============================================================

def get_due_recurring_transactions(
    as_of_date: date | None = None,
) -> list[dict]:
    """
    Return active recurring transactions owned by the
    current user whose next due date is today or earlier.
    """

    user_id = get_current_user_id()

    as_of_date = as_of_date or date.today()

    response = (
        get_table("recurring_transactions")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .lte(
            "next_due_date",
            as_of_date.isoformat(),
        )
        .order("next_due_date")
        .execute()
    )

    return response.data or []