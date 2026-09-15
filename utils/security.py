import bcrypt


def hash_password(password: str) -> str:
    """
    Create a secure bcrypt password hash.
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    password_bytes = password.encode("utf-8")

    password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return password_hash.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a stored bcrypt hash.
    """
    if not password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False