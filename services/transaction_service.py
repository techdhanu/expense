from datetime import date
from decimal import Decimal

from database.queries import get_table
from utils.constants import TRANSACTION_TYPES
from utils.validators import validate_amount


def _decimal(value) -> Decimal:
    """Convert a value to Decimal safely."""
    return Decimal(str(value or "0.00"))


def get_all_transactions() -> list[dict]:
    """Return all transactions, newest first."""
    response = (
        get_table("transactions")
        .select("*")
        .order("transaction_date", desc=True)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def get_transaction(transaction_id: str) -> dict | None:
    """Return one transaction by ID."""
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
    """Return transactions within an inclusive date range."""

    response = (
        get_table("transactions")
        .select("*")
        .gte("transaction_date", start_date.isoformat())
        .lte("transaction_date", end_date.isoformat())
        .order("transaction_date", desc=True)
        .execute()
    )

    return response.data or []


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

    This function performs validation before inserting data.
    """

    if transaction_type not in TRANSACTION_TYPES:
        raise ValueError(
            f"Invalid transaction type: {transaction_type}"
        )

    amount = validate_amount(amount)

    if not isinstance(transaction_date, date):
        raise ValueError("Invalid transaction date.")

    if (
        source_account_id
        and destination_account_id
        and source_account_id == destination_account_id
    ):
        raise ValueError(
            "Source and destination accounts must be different."
        )

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

    transaction_data = {
        "transaction_date": transaction_date.isoformat(),
        "transaction_type": transaction_type,
        "amount": str(amount),
        "source_account_id": source_account_id,
        "destination_account_id": destination_account_id,
        "category_id": category_id,
        "payment_method": payment_method,
        "person_id": person_id,
        "description": description.strip() if description else None,
        "notes": notes.strip() if notes else None,
    }

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

    Important:
    Transfers are NOT income or expenses.
    They only move money between accounts.
    """

    if from_account_id == to_account_id:
        raise ValueError(
            "Source and destination accounts must be different."
        )

    transaction = create_transaction(
        transaction_date=transaction_date,
        transaction_type="internal_transfer",
        amount=amount,
        source_account_id=from_account_id,
        destination_account_id=to_account_id,
        description=description,
        notes=notes,
    )

    transfer_data = {
        "transaction_id": transaction["id"],
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount": str(validate_amount(amount)),
        "transfer_date": transaction_date.isoformat(),
        "description": description.strip()
        if description
        else None,
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


def update_transaction(
    transaction_id: str,
    updates: dict,
) -> dict:
    """
    Update an existing transaction and keep linked transfer
    data synchronized when applicable.
    """

    if not updates:
        raise ValueError("No changes were provided.")

    # Get the existing transaction first.
    existing_response = (
        get_table("transactions")
        .select("*")
        .eq("id", transaction_id)
        .execute()
    )

    if not existing_response.data:
        raise RuntimeError(
            "Transaction could not be found."
        )

    existing_transaction = existing_response.data[0]

    # Validate amount if it is being changed.
    if "amount" in updates:
        updates["amount"] = str(
            validate_amount(updates["amount"])
        )

    # Validate transaction type if it is being changed.
    if "transaction_type" in updates:
        if updates["transaction_type"] not in TRANSACTION_TYPES:
            raise ValueError(
                "Invalid transaction type."
            )

    # Update the main transaction.
    response = (
        get_table("transactions")
        .update(updates)
        .eq("id", transaction_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Transaction could not be updated."
        )

    updated_transaction = response.data[0]

    # Keep linked transfer synchronized.
    if existing_transaction["transaction_type"] == "internal_transfer":
        transfer_updates = {}

        if "amount" in updates:
            transfer_updates["amount"] = updates["amount"]

        if "transaction_date" in updates:
            transfer_updates["transfer_date"] = updates[
                "transaction_date"
            ]

        if "description" in updates:
            transfer_updates["description"] = updates[
                "description"
            ]

        if "notes" in updates:
            # transfers table does not currently have a notes field.
            pass

        if transfer_updates:
            (
                get_table("transfers")
                .update(transfer_updates)
                .eq("transaction_id", transaction_id)
                .execute()
            )

    return updated_transaction

def delete_transaction(
    transaction_id: str,
) -> None:
    """
    Delete a transaction and its linked transfer record if applicable.
    """

    transaction = get_transaction(transaction_id)

    if transaction is None:
        raise ValueError("Transaction not found.")

    transaction_type = transaction["transaction_type"]

    # Transfers have a linked record in the transfers table.
    if transaction_type == "internal_transfer":

        transfer_response = (
            get_table("transfers")
            .select("id")
            .eq("transaction_id", transaction_id)
            .limit(1)
            .execute()
        )

        if transfer_response.data:
            (
                get_table("transfers")
                .delete()
                .eq("transaction_id", transaction_id)
                .execute()
            )

    # Delete the main transaction.
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