from decimal import Decimal, InvalidOperation
from datetime import date


def validate_amount(value) -> Decimal:
    """
    Validate and return a positive monetary amount.
    Uses Decimal to avoid floating-point errors.
    """
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Amount must be a valid number.") from exc

    if amount <= 0:
        raise ValueError("Amount must be greater than ₹0.")

    return amount.quantize(Decimal("0.01"))


def validate_required_text(value, field_name: str) -> str:
    """
    Validate a required text field.
    """
    if value is None:
        raise ValueError(f"{field_name} is required.")

    text = str(value).strip()

    if not text:
        raise ValueError(f"{field_name} is required.")

    return text


def validate_date(value) -> date:
    """
    Validate that a value is a date.
    """
    if not isinstance(value, date):
        raise ValueError("Please provide a valid date.")

    return value


def validate_different_accounts(
    source_account_id: str,
    destination_account_id: str,
) -> None:
    """
    Ensure a transfer does not use the same account as both source
    and destination.
    """
    if source_account_id == destination_account_id:
        raise ValueError(
            "Source and destination accounts must be different."
        )


def validate_transaction_type(transaction_type: str, allowed_types: list) -> str:
    """
    Validate a transaction type against the application's allowed types.
    """
    transaction_type = str(transaction_type).strip()

    if transaction_type not in allowed_types:
        raise ValueError(
            f"Invalid transaction type: {transaction_type}"
        )

    return transaction_type