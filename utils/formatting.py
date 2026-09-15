from decimal import Decimal, InvalidOperation


def to_decimal(value) -> Decimal:
    """
    Convert a value safely to Decimal.
    Never use float for financial calculations.
    """
    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid monetary value: {value}") from exc


def format_inr(value) -> str:
    """
    Format a monetary value as Indian Rupees.
    Example: ₹1,25,000.00
    """
    amount = to_decimal(value)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)

    formatted = f"{amount:,.2f}"

    return f"{sign}₹{formatted}"


def format_amount(value) -> str:
    """
    Format a monetary value without the currency symbol.
    """
    amount = to_decimal(value)
    return f"{amount:,.2f}"


def format_percentage(value) -> str:
    """
    Format a percentage value.
    """
    amount = to_decimal(value)
    return f"{amount:.1f}%"