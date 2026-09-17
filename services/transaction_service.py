from datetime import date
from decimal import Decimal

from database.queries import get_table
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


# =========================================================
# TRANSACTION READ OPERATIONS
# =========================================================

def get_all_transactions() -> list[dict]:
    """
    Return all transactions, newest first.
    """

    response = (
        get_table("transactions")
        .select("*")
        .order("transaction_date", desc=True)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def get_transaction(
    transaction_id: str,
) -> dict | None:
    """
    Return one transaction by ID.
    """

    if not transaction_id:
        raise ValueError("Transaction ID is required.")

    response = (
        get_table("transactions")
        .select("*")
        .eq("id", transaction_id)
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
    Return transactions within an inclusive date range.
    """

    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after end date."
        )

    response = (
        get_table("transactions")
        .select("*")
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
    Return transactions matching the supplied filters.

    Filtering is performed at the database level.
    """

    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after end date."
        )

    query = (
        get_table("transactions")
        .select("*")
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
        query = query.in_(
            "category_id",
            category_ids,
        )

    # -----------------------------------------------------
    # Person filter
    # -----------------------------------------------------
    if person_ids:
        query = query.in_(
            "person_id",
            person_ids,
        )

    # -----------------------------------------------------
    # Account filter
    #
    # An account may appear as either source or
    # destination, which is important for transfers.
    # -----------------------------------------------------
    if account_ids:

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
    Create a standard transaction.

    Performs application-level validation before inserting
    into PostgreSQL.
    """

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
        "transaction_date": transaction_date.isoformat(),
        "transaction_type": transaction_type,
        "amount": str(amount),
        "source_account_id": source_account_id,
        "destination_account_id": destination_account_id,
        "category_id": category_id,
        "payment_method": payment_method,
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
    transaction_date: date,
    amount,
    from_account_id: str,
    to_account_id: str,
    description: str | None = None,
    notes: str | None = None,
) -> dict:
    """
    Create an internal transfer.

    Transfers move money between accounts and are not
    treated as income or expenses.
    """

    if not from_account_id:
        raise ValueError(
            "Transfer requires a source account."
        )

    if not to_account_id:
        raise ValueError(
            "Transfer requires a destination account."
        )

    if from_account_id == to_account_id:
        raise ValueError(
            "Source and destination accounts must be different."
        )

    validated_amount = validate_amount(amount)

    transaction = create_transaction(
        transaction_date=transaction_date,
        transaction_type="internal_transfer",
        amount=validated_amount,
        source_account_id=from_account_id,
        destination_account_id=to_account_id,
        description=description,
        notes=notes,
    )

    transfer_data = {
        "transaction_id": transaction["id"],
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount": str(validated_amount),
        "transfer_date": transaction_date.isoformat(),
        "description": _clean_text(description),
    }

    response = (
        get_table("transfers")
        .insert(transfer_data)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Transfer record could not be created."
        )

    return transaction


# =========================================================
# TRANSACTION UPDATE
# =========================================================

def update_transaction(
    transaction_id: str,
    updates: dict,
) -> dict:
    """
    Safely update an existing transaction.

    Generic updates are intentionally restricted.

    Linked transaction types such as friend-money and
    savings contributions must be updated through their
    dedicated services so that related records remain
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

    # -----------------------------------------------------
    # Optional fields
    # -----------------------------------------------------
    if "category_id" in updates:
        clean_updates["category_id"] = (
            updates["category_id"]
        )

    if "payment_method" in updates:
        clean_updates["payment_method"] = (
            updates["payment_method"]
        )

    if not clean_updates:
        raise ValueError(
            "No valid changes were provided."
        )

    # -----------------------------------------------------
    # Update main transaction
    # -----------------------------------------------------
    response = (
        get_table("transactions")
        .update(clean_updates)
        .eq("id", transaction_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Transaction could not be updated."
        )

    updated_transaction = response.data[0]

    # -----------------------------------------------------
    # Synchronize linked transfer
    # -----------------------------------------------------
    if existing_type == "internal_transfer":

        transfer_updates = {}

        if "amount" in clean_updates:
            transfer_updates["amount"] = (
                clean_updates["amount"]
            )

        if "transaction_date" in clean_updates:
            transfer_updates["transfer_date"] = (
                clean_updates["transaction_date"]
            )

        if "description" in clean_updates:
            transfer_updates["description"] = (
                clean_updates["description"]
            )

        if transfer_updates:

            (
                get_table("transfers")
                .update(transfer_updates)
                .eq(
                    "transaction_id",
                    transaction_id,
                )
                .execute()
            )

    return updated_transaction


# =========================================================
# TRANSACTION DELETE
# =========================================================

def delete_transaction(
    transaction_id: str,
) -> None:
    """
    Safely delete a transaction.

    Transfer child records are removed before the main
    transaction because of the foreign-key relationship.

    Friend-money and savings-linked transactions are
    intentionally protected by the database/service layer
    and must be deleted through their dedicated workflows.
    """

    if not transaction_id:
        raise ValueError(
            "Transaction ID is required."
        )

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
    }

    if transaction_type in protected_types:
        raise ValueError(
            "This transaction is linked to another "
            "financial record and must be deleted through "
            "its dedicated service."
        )

    # -----------------------------------------------------
    # Delete linked transfer
    # -----------------------------------------------------
    if transaction_type == "internal_transfer":

        transfer_response = (
            get_table("transfers")
            .select("id")
            .eq(
                "transaction_id",
                transaction_id,
            )
            .limit(1)
            .execute()
        )

        if transfer_response.data:

            (
                get_table("transfers")
                .delete()
                .eq(
                    "transaction_id",
                    transaction_id,
                )
                .execute()
            )

    # -----------------------------------------------------
    # Delete main transaction
    # -----------------------------------------------------
    response = (
        get_table("transactions")
        .delete()
        .eq("id", transaction_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Transaction could not be deleted."
        )