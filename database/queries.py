from database.client import get_supabase_client


def get_table(table_name: str):
    """Return a Supabase table query object."""
    return get_supabase_client().table(table_name)


def get_app_users():
    """Fetch all application users."""
    return get_table("app_users").select("*").execute().data


def get_accounts():
    """Fetch all accounts."""
    return get_table("accounts").select("*").execute().data


def get_categories():
    """Fetch all categories."""
    return get_table("categories").select("*").execute().data


def get_transactions():
    """Fetch all transactions."""
    return get_table("transactions").select("*").execute().data