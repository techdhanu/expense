from datetime import date
from decimal import Decimal

from database.client import get_supabase_client
from database.queries import get_table
from services.authentication_service import get_current_user_id
from utils.constants import TRANSACTION_TYPES
from utils.validators import validate_amount


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _decimal(value) -> Decimal:
    """Convert a database numeric value safely to Decimal."""
    return Decimal(str(value or "0.00"))


def _clean_text(value: str | None) -> str | None:
    """Normalize optional text fields."""
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _validate_transaction_date(transaction_date) -> date:
    """Validate a transaction date."""
    if not isinstance(transaction_date, date):
        raise ValueError("Invalid transaction date.")

    return transaction_date


def _get_owned_account(
    account_id: str,
    require_active: bool = True,
) -> dict:
    """
    Return an account belonging to the currently logged-in user.

    This prevents one user from referencing another user's
    account UUID.
    """
    if not account_id:
        raise ValueError("Account ID is required.")

    user_id = get_current_user_id()

    query = (
        get_table("accounts")
        .select("*")
        .eq("id", account_id)
        .eq("user_id", user_id)
    )

    if require_active:
        query = query.eq("is_active", True)

    response = query.limit(1).execute()

    if not response.data:
        raise ValueError(
            "Account not found or does not belong to the current user."
        )

    return response.data[0]


def _validate_owned_category(
    category_id: str | None,
) -> None:
    """
    Validate that a category belongs to the current user.

    None is allowed because category is optional for some
    transaction types.
    """
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
            "Category not found or does not belong to the current user."
        )


def _validate_owned_person(
    person_id: str | None,
) -> None:
    """
    Validate that a person belongs to the current user.

    None is allowed for transaction types that do not use
    a person.
    """
    if not person_id:
        return

    user_id = get_current_user_id()

    response = (
        get_table("people")
        .select("id")
        .eq("id", person_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Person not found or does not belong to the current user."
        )


# =========================================================
# TRANSACTION READ OPERATIONS
# =========================================================

def get_all_transactions() -> list[dict]:
    """
    Return all transactions belonging to the current user,
    newest first.
    """
    user_id = get_current_user_id()

    response = (
        get_table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("transaction_date", desc=True)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def get_transaction(
    transaction_id: str,
) -> dict | None:
    """
    Return one transaction belonging to the current user.

    A transaction belonging to another user is intentionally
    returned as not found.
    """
    if not transaction_id:
        raise ValueError("Transaction ID is required.")

    user_id = get_current_user_id()

    response = (
        get_table("transactions")
        .select("*")
        .eq("id", transaction_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_transactions_by_date_range(
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Return current-user transactions within an inclusive
    date range.
    """
    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after end date."
        )

    user_id = get_current_user_id()

    response = (
        get_table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .gte(
            "transaction_date",
            start_date.isoformat(),
        )
        .lte(
            "transaction_date",
            end_date.isoformat(),
        )
        .order("transaction_date", desc=True)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def get_filtered_transactions(
    start_date: date,
    end_date: date,
    transaction_types: list[str] | None = None,
    account_ids: list[str] | None = None,
    category_ids: list[str] | None = None,
    person_ids: list[str] | None = None,
) -> list[dict]:
    """
    Return current-user transactions matching the supplied
    filters.

    Filtering is performed at the database level.
    """
    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after end date."
        )

    user_id = get_current_user_id()

    query = (
        get_table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .gte(
            "transaction_date",
            start_date.isoformat(),
        )
        .lte(
            "transaction_date",
            end_date.isoformat(),
        )
    )

    # -----------------------------------------------------
    # Transaction type filter
    # -----------------------------------------------------
    if transaction_types:
        invalid_types = (
            set(transaction_types)
            - set(TRANSACTION_TYPES)
        )

        if invalid_types:
            raise ValueError(
                "Invalid transaction type(s): "
                + ", ".join(sorted(invalid_types))
            )

        query = query.in_(
            "transaction_type",
            transaction_types,
        )

    # -----------------------------------------------------
    # Category filter
    # -----------------------------------------------------
    if category_ids:
        for category_id in category_ids:
            _validate_owned_category(category_id)

        query = query.in_(
            "category_id",
            category_ids,
        )

    # -----------------------------------------------------
    # Person filter
    # -----------------------------------------------------
    if person_ids:
        for person_id in person_ids:
            _validate_owned_person(person_id)

        query = query.in_(
            "person_id",
            person_ids,
        )

    # -----------------------------------------------------
    # Account filter
    #
    # An account may appear as either source or destination.
    # -----------------------------------------------------
    if account_ids:
        for account_id in account_ids:
            _get_owned_account(
                account_id,
                require_active=False,
            )

        account_conditions = []

        for account_id in account_ids:
            account_conditions.append(
                f"source_account_id.eq.{account_id}"
            )

            account_conditions.append(
                f"destination_account_id.eq.{account_id}"
            )

        query = query.or_(
            ",".join(account_conditions)
        )

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    response = (
        query
        .order("transaction_date", desc=True)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# =========================================================
# CORE TRANSACTION CREATION
# =========================================================

def create_transaction(
    transaction_date: date,
    transaction_type: str,
    amount,
    source_account_id: str | None = None,
    destination_account_id: str | None = None,
    category_id: str | None = None,
    payment_method: str | None = None,
    person_id: str | None = None,
    description: str | None = None,
    notes: str | None = None,
) -> dict:
    """
    Create a standard transaction for the current user.

    All referenced accounts, categories and people are
    ownership-validated before insertion.
    """

    user_id = get_current_user_id()

    # -----------------------------------------------------
    # Transaction type
    # -----------------------------------------------------
    if transaction_type not in TRANSACTION_TYPES:
        raise ValueError(
            f"Invalid transaction type: {transaction_type}"
        )

    # -----------------------------------------------------
    # Amount
    # -----------------------------------------------------
    amount = validate_amount(amount)

    # -----------------------------------------------------
    # Date
    # -----------------------------------------------------
    transaction_date = _validate_transaction_date(
        transaction_date
    )

    # -----------------------------------------------------
    # Account validation
    # -----------------------------------------------------
    if (
        source_account_id
        and destination_account_id
        and source_account_id == destination_account_id
    ):
        raise ValueError(
            "Source and destination accounts must be different."
        )

    # Validate source account ownership.
    if source_account_id:
        _get_owned_account(
            source_account_id,
            require_active=True,
        )

    # Validate destination account ownership.
    if destination_account_id:
        _get_owned_account(
            destination_account_id,
            require_active=True,
        )

    # -----------------------------------------------------
    # Category / person ownership
    # -----------------------------------------------------
    _validate_owned_category(category_id)
    _validate_owned_person(person_id)

    # -----------------------------------------------------
    # Type-specific validation
    # -----------------------------------------------------

    if transaction_type == "income":

        if not source_account_id:
            raise ValueError(
                "Income must have a destination account."
            )

    elif transaction_type == "expense":

        if not source_account_id:
            raise ValueError(
                "Expense must have a source account."
            )

    elif transaction_type == "internal_transfer":

        if not source_account_id:
            raise ValueError(
                "Transfer requires a source account."
            )

        if not destination_account_id:
            raise ValueError(
                "Transfer requires a destination account."
            )

        if source_account_id == destination_account_id:
            raise ValueError(
                "Source and destination accounts must be different."
            )

    elif transaction_type == "friend_money_received":

        if not source_account_id:
            raise ValueError(
                "Friend money received requires an account."
            )

        if not person_id:
            raise ValueError(
                "Friend money received requires a person."
            )

    elif transaction_type == "friend_money_returned":

        if not source_account_id:
            raise ValueError(
                "Friend money returned requires an account."
            )

        if not person_id:
            raise ValueError(
                "Friend money returned requires a person."
            )

    elif transaction_type == "friend_money_lent":

        if not source_account_id:
            raise ValueError(
                "Money lent requires an account."
            )

        if not person_id:
            raise ValueError(
                "Money lent requires a person."
            )

    elif transaction_type == "friend_money_lent_returned":

        if not source_account_id:
            raise ValueError(
                "Money lent returned requires an account."
            )

        if not person_id:
            raise ValueError(
                "Money lent returned requires a person."
            )

    elif transaction_type == "balance_adjustment":

        if not source_account_id:
            raise ValueError(
                "Balance adjustment requires an account."
            )

    elif transaction_type == "savings_goal_contribution":

        if not source_account_id:
            raise ValueError(
                "Savings contribution requires an account."
            )

    # -----------------------------------------------------
    # Build transaction payload
    # -----------------------------------------------------
    transaction_data = {
        "user_id": user_id,
        "transaction_date": transaction_date.isoformat(),
        "transaction_type": transaction_type,
        "amount": str(amount),
        "source_account_id": source_account_id,
        "destination_account_id": destination_account_id,
        "category_id": category_id,
        "payment_method": _clean_text(payment_method),
        "person_id": person_id,
        "description": _clean_text(description),
        "notes": _clean_text(notes),
    }

    # -----------------------------------------------------
    # Insert
    # -----------------------------------------------------
    response = (
        get_table("transactions")
        .insert(transaction_data)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Transaction could not be created."
        )

    return response.data[0]


# =========================================================
# SPECIALIZED CREATION FUNCTIONS
# =========================================================

def create_income(
    transaction_date: date,
    amount,
    account_id: str,
    category_id: str | None = None,
    payment_method: str | None = None,
    description: str | None = None,
    notes: str | None = None,
) -> dict:
    """Create an income transaction."""

    return create_transaction(
        transaction_date=transaction_date,
        transaction_type="income",
        amount=amount,
        source_account_id=account_id,
        category_id=category_id,
        payment_method=payment_method,
        description=description,
        notes=notes,
    )


def create_expense(
    transaction_date: date,
    amount,
    account_id: str,
    category_id: str | None = None,
    payment_method: str | None = None,
    description: str | None = None,
    notes: str | None = None,
) -> dict:
    """Create an expense transaction."""

    return create_transaction(
        transaction_date=transaction_date,
        transaction_type="expense",
        amount=amount,
        source_account_id=account_id,
        category_id=category_id,
        payment_method=payment_method,
        description=description,
        notes=notes,
    )


def create_transfer(
    transaction_date,
    amount,
    from_account_id,
    to_account_id,
    description=None,
    notes=None,
):
    """
    Create an internal account transfer atomically.

    The transaction row and transfer row are created inside a single
    PostgreSQL transaction through the record_transfer_atomic RPC.

    Internal transfers are not income or expenses and therefore do not
    change the user's total overall balance.
    """
    user_id = get_current_user_id()

    # Preserve service-level validation before calling the RPC.
    if from_account_id is None:
        raise ValueError("Source account is required.")

    if to_account_id is None:
        raise ValueError("Destination account is required.")

    if from_account_id == to_account_id:
        raise ValueError("Source and destination accounts must be different.")

    amount = validate_amount(amount)

    # Preserve the existing service contract: transaction dates must be
    # actual date values, and Supabase RPC arguments must be JSON-serializable.
    transaction_date = _validate_transaction_date(transaction_date)

    # Validate ownership and active status at the service layer.
    _get_owned_account(from_account_id)
    _get_owned_account(to_account_id)

    # The database RPC repeats the ownership validation inside the
    # same PostgreSQL transaction, protecting against race conditions.
    response = get_supabase_client().rpc(
        "record_transfer_atomic",
        {
            "p_transaction_date": transaction_date.isoformat(),
            "p_amount": str(amount),
            "p_from_account_id": from_account_id,
            "p_to_account_id": to_account_id,
            "p_description": description,
            "p_notes": notes,
            "p_user_id": user_id,
        },
    ).execute()

    result = response.data

    if not result:
        raise RuntimeError("Failed to create transfer.")

    # The RPC returns JSONB containing the created transaction.
    # Remove the RPC-only transfer_id field so the public service
    # contract remains compatible with the existing function.
    result.pop("transfer_id", None)

    return result
# =========================================================
# TRANSACTION UPDATE
# =========================================================

def update_transaction(
    transaction_id: str,
    updates: dict,
) -> dict:
    """
    Safely update an existing transaction belonging to the
    current user.

    Generic updates are intentionally restricted.

    Linked transaction types such as friend-money, savings
    contributions and Money Lent must be updated through
    their dedicated services so related records remain
    financially consistent.
    """

    if not transaction_id:
        raise ValueError(
            "Transaction ID is required."
        )

    if not updates:
        raise ValueError(
            "No changes were provided."
        )

    user_id = get_current_user_id()

    # -----------------------------------------------------
    # Get existing transaction
    # -----------------------------------------------------
    existing_transaction = get_transaction(
        transaction_id
    )

    if existing_transaction is None:
        raise ValueError(
            "Transaction not found."
        )

    existing_type = existing_transaction[
        "transaction_type"
    ]

    # -----------------------------------------------------
    # Linked transaction protection
    # -----------------------------------------------------
    protected_types = {
        "friend_money_received",
        "friend_money_returned",
        "savings_goal_contribution",
        "friend_money_lent",
        "friend_money_lent_returned",
    }

    if existing_type in protected_types:
        raise ValueError(
            "This transaction is linked to another "
            "financial record and must be updated through "
            "its dedicated service."
        )

    # -----------------------------------------------------
    # Only allow safe editable fields
    # -----------------------------------------------------
    allowed_fields = {
        "transaction_date",
        "amount",
        "category_id",
        "payment_method",
        "description",
        "notes",
    }

    unexpected_fields = (
        set(updates) - allowed_fields
    )

    if unexpected_fields:
        raise ValueError(
            "Unsupported transaction field(s): "
            + ", ".join(sorted(unexpected_fields))
        )

    clean_updates = {}

    # -----------------------------------------------------
    # Date
    # -----------------------------------------------------
    if "transaction_date" in updates:

        transaction_date = _validate_transaction_date(
            updates["transaction_date"]
        )

        clean_updates[
            "transaction_date"
        ] = transaction_date.isoformat()

    # -----------------------------------------------------
    # Amount
    # -----------------------------------------------------
    if "amount" in updates:

        clean_updates["amount"] = str(
            validate_amount(
                updates["amount"]
            )
        )

    # -----------------------------------------------------
    # Text fields
    # -----------------------------------------------------
    if "description" in updates:
        clean_updates["description"] = _clean_text(
            updates["description"]
        )

    if "notes" in updates:
        clean_updates["notes"] = _clean_text(
            updates["notes"]
        )

    if "payment_method" in updates:
        clean_updates["payment_method"] = _clean_text(
            updates["payment_method"]
        )

    # -----------------------------------------------------
    # Category
    # -----------------------------------------------------
    if "category_id" in updates:

        category_id = updates["category_id"]

        _validate_owned_category(category_id)

        clean_updates["category_id"] = category_id

    # -----------------------------------------------------
    # Ensure there is something to update
    # -----------------------------------------------------
    if not clean_updates:
        raise ValueError(
            "No valid changes were provided."
        )

    # -----------------------------------------------------
    # Update transaction
    # -----------------------------------------------------
    if existing_type == "internal_transfer":
        """
        Internal transfers have two linked financial records:
            1. transactions
            2. transfers

        Use the atomic PostgreSQL RPC so both records are updated
        inside the same database transaction.
        """

        # Preserve existing values for fields that were not edited.
        transaction_date = existing_transaction["transaction_date"]
        amount = existing_transaction["amount"]
        category_id = existing_transaction.get("category_id")
        payment_method = existing_transaction.get("payment_method")
        description = existing_transaction.get("description")
        notes = existing_transaction.get("notes")

        # Apply requested changes.
        if "transaction_date" in clean_updates:
            transaction_date = clean_updates["transaction_date"]

        if "amount" in clean_updates:
            amount = clean_updates["amount"]

        if "category_id" in clean_updates:
            category_id = clean_updates["category_id"]

        if "payment_method" in clean_updates:
            payment_method = clean_updates["payment_method"]

        if "description" in clean_updates:
            description = clean_updates["description"]

        if "notes" in clean_updates:
            notes = clean_updates["notes"]

        response = get_supabase_client().rpc(
            "update_transfer_atomic",
            {
                "p_transaction_id": transaction_id,
                "p_transaction_date": transaction_date,
                "p_amount": str(amount),
                "p_category_id": category_id,
                "p_payment_method": payment_method,
                "p_description": description,
                "p_notes": notes,
                "p_user_id": user_id,
            },
        ).execute()

        result = response.data

        if not result:
            raise RuntimeError(
                "Transfer could not be updated."
            )

        # The RPC returns transfer_id for internal verification,
        # but preserve the existing service return contract.
        result.pop("transfer_id", None)

        return result

    # -----------------------------------------------------
    # Update non-transfer transaction
    # -----------------------------------------------------
    response = (
        get_table("transactions")
        .update(clean_updates)
        .eq("id", transaction_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Transaction could not be updated."
        )

    return response.data[0]


# =========================================================
# TRANSACTION DELETE
# =========================================================

def delete_transaction(
    transaction_id: str,
) -> None:
    """
    Safely delete a transaction belonging to the current user.

    Transfer child records are removed before the main
    transaction because of the foreign-key relationship.

    Friend-money, savings-linked and Money Lent transactions
    are intentionally protected.
    """

    if not transaction_id:
        raise ValueError(
            "Transaction ID is required."
        )

    user_id = get_current_user_id()

    # -----------------------------------------------------
    # Get current user's transaction
    # -----------------------------------------------------
    transaction = get_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            "Transaction not found."
        )

    transaction_type = transaction[
        "transaction_type"
    ]

    # -----------------------------------------------------
    # Protect linked financial records
    # -----------------------------------------------------
    protected_types = {
        "friend_money_received",
        "friend_money_returned",
        "savings_goal_contribution",
        "friend_money_lent",
        "friend_money_lent_returned",
    }

    if transaction_type in protected_types:
        raise ValueError(
            "This transaction is linked to another "
            "financial record and must be deleted through "
            "its dedicated service."
        )

    # -----------------------------------------------------
    # Delete internal transfer atomically
    # -----------------------------------------------------
    if transaction_type == "internal_transfer":
        response = get_supabase_client().rpc(
            "delete_transfer_atomic",
            {
                "p_transaction_id": transaction_id,
                "p_user_id": user_id,
            },
        ).execute()

        if not response.data:
            raise RuntimeError(
                "Transfer could not be deleted."
            )

        return None

    # -----------------------------------------------------
    # Delete main transaction
    # -----------------------------------------------------
    response = (
        get_table("transactions")
        .delete()
        .eq("id", transaction_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Transaction could not be deleted."
        )
