from decimal import Decimal

from database.queries import get_table
from utils.calculations import calculate_total_balance
from utils.constants import DEFAULT_ACCOUNTS
from utils.validators import validate_amount


def get_all_accounts() -> list[dict]:
    """Return all active accounts."""
    response = (
        get_table("accounts")
        .select("*")
        .eq("is_active", True)
        .order("name")
        .execute()
    )

    return response.data or []


def get_account(account_id: str) -> dict | None:
    """Return a single account by ID."""
    response = (
        get_table("accounts")
        .select("*")
        .eq("id", account_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_account(
    name: str,
    account_type: str = "bank",
    opening_balance=Decimal("0.00"),
) -> dict:
    """Create a new account."""

    name = name.strip()

    if not name:
        raise ValueError("Account name is required.")

    if account_type not in {"bank", "cash", "other"}:
        raise ValueError("Invalid account type.")

    opening_balance = validate_amount(
        opening_balance
    ) if Decimal(str(opening_balance)) > 0 else Decimal("0.00")

    existing = (
        get_table("accounts")
        .select("id")
        .eq("name", name)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise ValueError(
            f"Account '{name}' already exists."
        )

    response = (
        get_table("accounts")
        .insert(
            {
                "name": name,
                "account_type": account_type,
                "opening_balance": str(opening_balance),
                "is_active": True,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError("Account could not be created.")

    return response.data[0]


def ensure_default_accounts() -> list[dict]:
    """
    Ensure the three required default accounts exist.

    Existing accounts are preserved.
    Missing default accounts are created with ₹0 opening balance.
    """

    existing_accounts = get_all_accounts()

    existing_names = {
        account["name"]
        for account in existing_accounts
    }

    for default_account in DEFAULT_ACCOUNTS:

        if default_account["name"] not in existing_names:
            create_account(
                name=default_account["name"],
                account_type=default_account["account_type"],
                opening_balance=Decimal("0.00"),
            )

    return get_all_accounts()


def get_total_opening_balance(
    accounts: list[dict] | None = None,
) -> Decimal:
    """Return the combined opening balance."""
    accounts = accounts if accounts is not None else get_all_accounts()

    return calculate_total_balance(
        account.get("opening_balance", "0.00")
        for account in accounts
    )


def deactivate_account(account_id: str) -> None:
    """
    Deactivate an account instead of physically deleting it.
    """

    account = get_account(account_id)

    if account is None:
        raise ValueError("Account not found.")

    response = (
        get_table("accounts")
        .update({"is_active": False})
        .eq("id", account_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError("Account could not be deactivated.")

def get_account_balance(account_id: str) -> Decimal:
    """
    Calculate the current balance for one account.

    Rules:
    - Income increases balance.
    - Expense decreases balance.
    - Friend money received increases bank balance.
    - Friend money returned decreases bank balance.
    - Transfer in increases balance.
    - Transfer out decreases balance.
    - Savings contribution decreases source account balance.
    - Balance adjustment is applied according to its amount.
    """

    account = get_account(account_id)

    if account is None:
        raise ValueError("Account not found.")

    balance = Decimal(
        str(account.get("opening_balance", "0.00"))
    )

    response = (
        get_table("transactions")
        .select(
            "transaction_type, amount, "
            "source_account_id, destination_account_id"
        )
        .or_(
            f"source_account_id.eq.{account_id},"
            f"destination_account_id.eq.{account_id}"
        )
        .execute()
    )

    for transaction in response.data or []:

        transaction_type = transaction["transaction_type"]
        amount = Decimal(
            str(transaction["amount"])
        )

        source_id = transaction.get(
            "source_account_id"
        )

        destination_id = transaction.get(
            "destination_account_id"
        )

        if transaction_type == "income":
            if destination_id == account_id or source_id == account_id:
                balance += amount

        elif transaction_type == "expense":
            if source_id == account_id:
                balance -= amount

        elif transaction_type == "friend_money_received":
            if source_id == account_id:
                balance += amount

        elif transaction_type == "friend_money_returned":
            if source_id == account_id:
                balance -= amount

        elif transaction_type == "internal_transfer":
            if source_id == account_id:
                balance -= amount

            if destination_id == account_id:
                balance += amount

        elif transaction_type == "balance_adjustment":
            if source_id == account_id:
                balance += amount

        elif transaction_type == "savings_goal_contribution":
            if source_id == account_id:
                balance -= amount

    return balance.quantize(Decimal("0.01"))


def get_all_account_balances() -> list[dict]:
    """
    Return all active accounts with their calculated balances.
    """

    accounts = get_all_accounts()

    result = []

    for account in accounts:
        balance = get_account_balance(
            account["id"]
        )

        result.append(
            {
                **account,
                "current_balance": balance,
            }
        )

    return result


def get_total_current_balance() -> Decimal:
    """
    Return the combined balance across all accounts.

    Internal transfers cancel each other out when all accounts
    are considered together.
    """

    balances = get_all_account_balances()

    total = Decimal("0.00")

    for account in balances:
        total += account["current_balance"]

    return total.quantize(Decimal("0.01"))