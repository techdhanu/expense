from database.queries import get_table
from services.authentication_service import get_current_user_id
from utils.validators import validate_required_text


DEFAULT_CATEGORIES = [
    # Income
    {"name": "Salary", "category_type": "income"},
    {"name": "Freelance", "category_type": "income"},
    {"name": "Interest", "category_type": "income"},
    {"name": "Other Income", "category_type": "income"},

    # Expenses
    {"name": "Food", "category_type": "expense"},
    {"name": "Groceries", "category_type": "expense"},
    {"name": "Transportation", "category_type": "expense"},
    {"name": "Shopping", "category_type": "expense"},
    {"name": "Bills & Utilities", "category_type": "expense"},
    {"name": "Rent", "category_type": "expense"},
    {"name": "Healthcare", "category_type": "expense"},
    {"name": "Entertainment", "category_type": "expense"},
    {"name": "Education", "category_type": "expense"},
    {"name": "Personal Care", "category_type": "expense"},
    {"name": "Travel", "category_type": "expense"},
    {"name": "Other Expense", "category_type": "expense"},
]


def get_all_categories():
    """Return all active categories for the current user."""

    user_id = get_current_user_id()

    response = (
        get_table("categories")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("category_type")
        .order("name")
        .execute()
    )

    return response.data or []


def get_categories_by_type(category_type: str):
    """Return active categories of a specific type for the current user."""

    user_id = get_current_user_id()

    category_type = validate_required_text(
        category_type,
        "Category type",
    )

    if category_type not in {"income", "expense"}:
        raise ValueError(
            "Category type must be income or expense."
        )

    response = (
        get_table("categories")
        .select("*")
        .eq("user_id", user_id)
        .eq("category_type", category_type)
        .eq("is_active", True)
        .order("name")
        .execute()
    )

    return response.data or []


def get_category(category_id: str):
    """Return one category belonging to the current user."""

    user_id = get_current_user_id()

    response = (
        get_table("categories")
        .select("*")
        .eq("id", category_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


def create_category(
    name: str,
    category_type: str,
):
    """Create a category for the current user."""

    user_id = get_current_user_id()

    name = validate_required_text(
        name,
        "Category name",
    )

    category_type = validate_required_text(
        category_type,
        "Category type",
    )

    if category_type not in {"income", "expense"}:
        raise ValueError(
            "Category type must be income or expense."
        )

    existing = (
        get_table("categories")
        .select("id")
        .eq("user_id", user_id)
        .eq("name", name)
        .eq("category_type", category_type)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise ValueError(
            "Category already exists."
        )

    response = (
        get_table("categories")
        .insert(
            {
                "user_id": user_id,
                "name": name,
                "category_type": category_type,
                "is_active": True,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Category could not be created."
        )

    return response.data[0]


def ensure_default_categories():
    """
    Create missing default categories for the current user.

    Safe to run multiple times because existing categories
    are skipped.
    """

    user_id = get_current_user_id()

    response = (
        get_table("categories")
        .select("name, category_type")
        .eq("user_id", user_id)
        .execute()
    )

    existing = response.data or []

    existing_keys = {
        (
            category["name"],
            category["category_type"],
        )
        for category in existing
    }

    created = []

    for category in DEFAULT_CATEGORIES:
        key = (
            category["name"],
            category["category_type"],
        )

        if key in existing_keys:
            continue

        created.append(
            create_category(
                category["name"],
                category["category_type"],
            )
        )

    return get_all_categories()


def deactivate_category(
    category_id: str,
):
    """
    Deactivate a category belonging to the current user
    without deleting historical data.
    """

    user_id = get_current_user_id()

    category = get_category(category_id)

    if category is None:
        raise ValueError(
            "Category not found."
        )

    response = (
        get_table("categories")
        .update(
            {
                "is_active": False,
            }
        )
        .eq("id", category_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Category could not be deactivated."
        )

    return response.data[0]