from decimal import Decimal, InvalidOperation

from database.queries import get_table
from utils.calculations import calculate_total_balance
from utils.constants import DEFAULT_ACCOUNTS
from utils.validators import validate_amount


# =========================================================
# CONSTANTS
# =========================================================

VALID_ACCOUNT_TYPES = {
    "bank",
    "cash",
    "other",
}

ZERO = Decimal("0.00")


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _to_decimal(value) -> Decimal:
    """
    Convert a monetary value to Decimal safely.

    Never use float arithmetic for financial values.
    """

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(
            "Invalid monetary value."
        ) from exc


def _validate_account_id(account_id: str) -> str:
    """
    Validate and normalize an account ID.
    """

    if not isinstance(account_id, str):
        raise ValueError("Account ID is required.")

    account_id = account_id.strip()

    if not account_id:
        raise ValueError("Account ID is required.")

    return account_id


def _validate_account_type(account_type: str) -> str:
    """
    Validate and normalize account type.
    """

    if not isinstance(account_type, str):
        raise ValueError("Account type is required.")

    account_type = account_type.strip().lower()

    if account_type not in VALID_ACCOUNT_TYPES:
        raise ValueError(
            "Invalid account type. "
            "Allowed types: bank, cash, other."
        )

    return account_type


def _validate_account_name(name: str) -> str:
    """
    Validate and normalize account name.
    """

    if not isinstance(name, str):
        raise ValueError("Account name is required.")

    name = name.strip()

    if not name:
        raise ValueError("Account name is required.")

    return name


# =========================================================
# GET ALL ACTIVE ACCOUNTS
# =========================================================

def get_all_accounts() -> list[dict]:
    """
    Return all active accounts.

    Inactive accounts are intentionally excluded from
    normal account selection.
    """

    response = (
        get_table("accounts")
        .select("*")
        .eq("is_active", True)
        .order("name")
        .execute()
    )

    return response.data or []


# =========================================================
# GET SINGLE ACCOUNT
# =========================================================

def get_account(account_id: str) -> dict | None:
    """
    Return a single account by ID.

    This includes inactive accounts so that historical
    transactions can still reference them safely.
    """

    account_id = _validate_account_id(account_id)

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


# =========================================================
# CREATE ACCOUNT
# =========================================================

def create_account(
    name: str,
    account_type: str = "bank",
    opening_balance=ZERO,
) -> dict:
    """
    Create a new active account.

    Opening balance cannot be negative.
    """

    name = _validate_account_name(name)
    account_type = _validate_account_type(account_type)

    opening_balance = _to_decimal(opening_balance)

    if opening_balance < ZERO:
        raise ValueError(
            "Opening balance cannot be negative."
        )

    if opening_balance > ZERO:
        opening_balance = validate_amount(
            opening_balance
        )
    else:
        opening_balance = ZERO

    # -----------------------------------------------------
    # CHECK DUPLICATE ACCOUNT NAME
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CREATE ACCOUNT
    # -----------------------------------------------------

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
        raise RuntimeError(
            "Account could not be created."
        )

    return response.data[0]


# =========================================================
# ENSURE DEFAULT ACCOUNTS
# =========================================================

def ensure_default_accounts() -> list[dict]:
    """
    Ensure the required default accounts exist.

    Existing accounts are preserved.
    Missing accounts are created with ₹0 opening balance.
    """

    existing_accounts = get_all_accounts()

    existing_names = {
        account["name"]
        for account in existing_accounts
        if account.get("name")
    }

    for default_account in DEFAULT_ACCOUNTS:

        if default_account["name"] not in existing_names:

            create_account(
                name=default_account["name"],
                account_type=default_account["account_type"],
                opening_balance=ZERO,
            )

    return get_all_accounts()


# =========================================================
# GET TOTAL OPENING BALANCE
# =========================================================

def get_total_opening_balance(
    accounts: list[dict] | None = None,
) -> Decimal:
    """
    Return the combined opening balance of the supplied
    accounts or all active accounts.
    """

    accounts = (
        accounts
        if accounts is not None
        else get_all_accounts()
    )

    return calculate_total_balance(
        _to_decimal(
            account.get(
                "opening_balance",
                ZERO,
            )
        )
        for account in accounts
    )


# =========================================================
# DEACTIVATE ACCOUNT
# =========================================================

def deactivate_account(
    account_id: str,
) -> None:
    """
    Deactivate an account instead of physically deleting it.

    Historical transaction records remain intact.
    """

    account_id = _validate_account_id(account_id)

    account = get_account(account_id)

    if account is None:
        raise ValueError(
            "Account not found."
        )

    if not account.get("is_active", False):
        raise ValueError(
            "Account is already inactive."
        )

    response = (
        get_table("accounts")
        .update(
            {
                "is_active": False,
            }
        )
        .eq("id", account_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Account could not be deactivated."
        )


# =========================================================
# GET ACCOUNT BALANCE
# =========================================================

def get_account_balance(
    account_id: str,
) -> Decimal:
    """
    Calculate the current balance for one account.

    Balance rules:

    Income
        increases balance.

    Expense
        decreases balance.

    Friend money received
        increases balance.

    Friend money returned
        decreases balance.

    Internal transfer
        decreases source account
        increases destination account.

    Savings contribution
        decreases source account.

    Money lent
        decreases source account.

    Money lent returned
        increases source account.

    Balance adjustment
        applies the adjustment amount.
    """

    account_id = _validate_account_id(account_id)

    account = get_account(account_id)

    if account is None:
        raise ValueError(
            "Account not found."
        )

    balance = _to_decimal(
        account.get(
            "opening_balance",
            ZERO,
        )
    )

    response = (
        get_table("transactions")
        .select(
            "transaction_type, amount, "
            "source_account_id, "
            "destination_account_id"
        )
        .or_(
            f"source_account_id.eq.{account_id},"
            f"destination_account_id.eq.{account_id}"
        )
        .execute()
    )

    for transaction in response.data or []:

        transaction_type = transaction.get(
            "transaction_type"
        )

        amount = _to_decimal(
            transaction.get(
                "amount",
                ZERO,
            )
        )

        source_id = transaction.get(
            "source_account_id"
        )

        destination_id = transaction.get(
            "destination_account_id"
        )

        # -------------------------------------------------
        # INCOME
        # -------------------------------------------------

        if transaction_type == "income":

            if (
                destination_id == account_id
                or source_id == account_id
            ):
                balance += amount

        # -------------------------------------------------
        # EXPENSE
        # -------------------------------------------------

        elif transaction_type == "expense":

            if source_id == account_id:
                balance -= amount

        # -------------------------------------------------
        # FRIEND MONEY RECEIVED
        # -------------------------------------------------

        elif transaction_type == "friend_money_received":

            if source_id == account_id:
                balance += amount

        # -------------------------------------------------
        # FRIEND MONEY RETURNED
        # -------------------------------------------------

        elif transaction_type == "friend_money_returned":

            if source_id == account_id:
                balance -= amount

        # -------------------------------------------------
        # INTERNAL TRANSFER
        # -------------------------------------------------

        elif transaction_type == "internal_transfer":

            if source_id == account_id:
                balance -= amount

            if destination_id == account_id:
                balance += amount

        # -------------------------------------------------
        # BALANCE ADJUSTMENT
        # -------------------------------------------------

        elif transaction_type == "balance_adjustment":

            if source_id == account_id:
                balance += amount

        # -------------------------------------------------
        # SAVINGS GOAL CONTRIBUTION
        # -------------------------------------------------

        elif transaction_type == "savings_goal_contribution":

            if source_id == account_id:
                balance -= amount

        # -------------------------------------------------
        # MONEY LENT
        # -------------------------------------------------

        elif transaction_type == "friend_money_lent":

            if source_id == account_id:
                balance -= amount

        # -------------------------------------------------
        # MONEY LENT RETURNED
        # -------------------------------------------------

        elif transaction_type == "friend_money_lent_returned":

            if source_id == account_id:
                balance += amount

    return balance.quantize(
        Decimal("0.01")
    )


# =========================================================
# GET ALL ACCOUNT BALANCES
# =========================================================

def get_all_account_balances() -> list[dict]:
    """
    Return all active accounts with their calculated
    current balances.
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


# =========================================================
# GET TOTAL CURRENT BALANCE
# =========================================================

def get_total_current_balance() -> Decimal:
    """
    Return the combined current balance across all
    active accounts.

    Internal transfers cancel each other when all
    accounts are considered together.
    """

    balances = get_all_account_balances()

    total = ZERO

    for account in balances:

        total += _to_decimal(
            account.get(
                "current_balance",
                ZERO,
            )
        )

    return total.quantize(
        Decimal("0.01")
    )
