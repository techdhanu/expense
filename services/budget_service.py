from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.authentication_service import get_current_user_id
from utils.validators import validate_amount


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _validate_owned_category(category_id: str) -> dict:
    """
    Return a category belonging to the currently logged-in user.
    """

    if not category_id:
        raise ValueError("Category is required.")

    user_id = get_current_user_id()

    response = (
        get_table("categories")
        .select("*")
        .eq("id", category_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Category not found or does not belong to the current user."
        )

    return response.data[0]


def _get_owned_budget(budget_id: str) -> dict:
    """
    Return a budget belonging to the current user.
    """

    if not budget_id:
        raise ValueError("Budget ID is required.")

    user_id = get_current_user_id()

    response = (
        get_table("budgets")
        .select("*")
        .eq("id", budget_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Budget not found or does not belong to the current user."
        )

    return response.data[0]


# ============================================================
# BUDGET READ OPERATIONS
# ============================================================

def get_all_budgets(
    month: int | None = None,
    year: int | None = None,
) -> list[dict]:
    """
    Return budgets belonging to the current user,
    optionally filtered by month and year.
    """

    user_id = get_current_user_id()

    query = (
        get_table("budgets")
        .select("*")
        .eq("user_id", user_id)
        .order("budget_year", desc=True)
        .order("budget_month", desc=True)
    )

    if month is not None:
        query = query.eq(
            "budget_month",
            month,
        )

    if year is not None:
        query = query.eq(
            "budget_year",
            year,
        )

    response = query.execute()

    return response.data or []


def get_budget(
    category_id: str,
    month: int,
    year: int,
) -> dict | None:
    """
    Return the budget for a category and month,
    only if it belongs to the current user.
    """

    user_id = get_current_user_id()

    _validate_owned_category(category_id)

    response = (
        get_table("budgets")
        .select("*")
        .eq("user_id", user_id)
        .eq("category_id", category_id)
        .eq("budget_month", month)
        .eq("budget_year", year)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


# ============================================================
# BUDGET CREATION
# ============================================================

def create_budget(
    category_id: str,
    month: int,
    year: int,
    amount,
) -> dict:
    """Create a monthly category budget for the current user."""

    user_id = get_current_user_id()

    if not category_id:
        raise ValueError("Category is required.")

    if month < 1 or month > 12:
        raise ValueError(
            "Month must be between 1 and 12."
        )

    if year < 2000:
        raise ValueError(
            "Invalid year."
        )

    amount = validate_amount(amount)

    # --------------------------------------------------------
    # Category ownership
    # --------------------------------------------------------
    _validate_owned_category(category_id)

    # --------------------------------------------------------
    # Duplicate check is user-scoped
    # --------------------------------------------------------
    existing = get_budget(
        category_id,
        month,
        year,
    )

    if existing:
        raise ValueError(
            "A budget already exists for this category and month."
        )

    # --------------------------------------------------------
    # Create budget
    # --------------------------------------------------------
    response = (
        get_table("budgets")
        .insert(
            {
                "user_id": user_id,
                "category_id": category_id,
                "budget_month": month,
                "budget_year": year,
                "budget_amount": str(amount),
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Budget could not be created."
        )

    return response.data[0]


# ============================================================
# BUDGET UPDATE
# ============================================================

def update_budget(
    budget_id: str,
    amount,
) -> dict:
    """
    Update an existing budget amount belonging to
    the current user.
    """

    amount = validate_amount(amount)

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Ownership check
    # --------------------------------------------------------
    _get_owned_budget(budget_id)

    # --------------------------------------------------------
    # Update only current user's budget
    # --------------------------------------------------------
    response = (
        get_table("budgets")
        .update(
            {
                "budget_amount": str(amount),
            }
        )
        .eq("id", budget_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Budget could not be updated."
        )

    return response.data[0]


# ============================================================
# BUDGET DELETE
# ============================================================

def delete_budget(
    budget_id: str,
) -> None:
    """Delete a budget belonging to the current user."""

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Ownership check
    # --------------------------------------------------------
    _get_owned_budget(budget_id)

    # --------------------------------------------------------
    # Delete only current user's budget
    # --------------------------------------------------------
    response = (
        get_table("budgets")
        .delete()
        .eq("id", budget_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Budget could not be deleted."
        )


# ============================================================
# CATEGORY EXPENSE CALCULATION
# ============================================================

def get_category_expense_total(
    category_id: str,
    start_date: date,
    end_date: date,
) -> Decimal:
    """
    Calculate total expenses for a category in a date range.

    Only transactions belonging to the current user are
    considered.
    """

    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after end date."
        )

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Category ownership
    # --------------------------------------------------------
    _validate_owned_category(category_id)

    # --------------------------------------------------------
    # User-scoped transaction query
    # --------------------------------------------------------
    response = (
        get_table("transactions")
        .select("amount")
        .eq("user_id", user_id)
        .eq("transaction_type", "expense")
        .eq("category_id", category_id)
        .gte(
            "transaction_date",
            start_date.isoformat(),
        )
        .lte(
            "transaction_date",
            end_date.isoformat(),
        )
        .execute()
    )

    total = Decimal("0.00")

    for transaction in response.data or []:
        total += Decimal(
            str(transaction["amount"])
        )

    return total.quantize(
        Decimal("0.01")
    )


# ============================================================
# BUDGET STATUS
# ============================================================

def get_budget_status(
    budget: dict,
    spent: Decimal,
) -> dict:
    """Return calculated budget status."""

    budget_amount = Decimal(
        str(budget["budget_amount"])
    )

    spent = Decimal(str(spent))

    remaining = budget_amount - spent

    if budget_amount > 0:
        percentage = (
            spent / budget_amount
        ) * Decimal("100")
    else:
        percentage = Decimal("0.00")

    return {
        "budget_amount": budget_amount.quantize(
            Decimal("0.01")
        ),
        "spent": spent.quantize(
            Decimal("0.01")
        ),
        "remaining": remaining.quantize(
            Decimal("0.01")
        ),
        "percentage": percentage.quantize(
            Decimal("0.01")
        ),
        "exceeded": spent > budget_amount,
    }