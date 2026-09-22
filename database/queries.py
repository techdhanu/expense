from database.client import get_supabase_client


def get_table(table_name: str):
    """Return a Supabase table query object."""
    return get_supabase_client().table(table_name)


def get_app_users():
    """
    Fetch all application users.

    This is intentionally global because authentication
    requires access to application-user records.
    """
    return (
        get_table("app_users")
        .select("*")
        .execute()
        .data
    )


def get_accounts():
    """Fetch only the current user's accounts."""
    from services.authentication_service import get_current_user_id

    user_id = get_current_user_id()

    return (
        get_table("accounts")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )


def get_categories():
    """Fetch only the current user's categories."""
    from services.authentication_service import get_current_user_id

    user_id = get_current_user_id()

    return (
        get_table("categories")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )


def get_transactions():
    """Fetch only the current user's transactions."""
    from services.authentication_service import get_current_user_id

    user_id = get_current_user_id()

    return (
        get_table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )