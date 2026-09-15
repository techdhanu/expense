from database.queries import get_table
from utils.security import hash_password, verify_password


def create_user(username: str, password: str) -> dict:
    """
    Create a new application user with a hashed password.
    """
    username = username.strip()

    if not username:
        raise ValueError("Username is required.")

    if not password:
        raise ValueError("Password is required.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    existing = (
        get_table("app_users")
        .select("id")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise ValueError("Username already exists.")

    password_hash = hash_password(password)

    response = (
        get_table("app_users")
        .insert(
            {
                "username": username,
                "password_hash": password_hash,
                "is_active": True,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError("User could not be created.")

    return response.data[0]


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Authenticate a user using username and password.

    Returns the user record when authentication succeeds.
    Returns None when credentials are invalid.
    """
    username = username.strip()

    if not username or not password:
        return None

    response = (
        get_table("app_users")
        .select("id, username, password_hash, is_active")
        .eq("username", username)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    user = response.data[0]

    if not verify_password(
        password,
        user["password_hash"],
    ):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
    }