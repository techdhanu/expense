import pytest

from services.authentication_service import (
    authenticate_user,
    create_user,
)


# =========================================================
# TEST USER
# =========================================================

TEST_USERNAME = "pytest_user"
TEST_PASSWORD = "PytestPassword123!"


# =========================================================
# AUTHENTICATED TEST USER FIXTURE
# =========================================================

@pytest.fixture(autouse=True)
def authenticated_test_user(monkeypatch):
    """
    Provide a dedicated authenticated user ID to all
    user-scoped services during pytest.

    This intentionally does not depend on Streamlit's
    session state because pytest runs outside Streamlit's
    normal ScriptRunContext.
    """

    # -----------------------------------------------------
    # Get or create dedicated pytest user
    # -----------------------------------------------------

    user = authenticate_user(
        TEST_USERNAME,
        TEST_PASSWORD,
    )

    if user is None:
        user = create_user(
            TEST_USERNAME,
            TEST_PASSWORD,
        )

    if not user:
        raise RuntimeError(
            "Could not create or authenticate pytest user."
        )

    user_id = str(user["id"])

    # -----------------------------------------------------
    # Import modules whose services use
    # get_current_user_id directly.
    # -----------------------------------------------------

    import services.account_service as account_service
    import services.transaction_service as transaction_service
    import services.category_service as category_service
    import services.budget_service as budget_service
    import services.friend_money_service as friend_money_service
    import services.savings_service as savings_service
    import services.recurring_service as recurring_service
    import services.backup_service as backup_service

    # -----------------------------------------------------
    # Replace get_current_user_id() inside each service
    # with the dedicated pytest user's ID.
    # -----------------------------------------------------

    monkeypatch.setattr(
        account_service,
        "get_current_user_id",
        lambda: user_id,
    )

    monkeypatch.setattr(
        transaction_service,
        "get_current_user_id",
        lambda: user_id,
    )

    monkeypatch.setattr(
        category_service,
        "get_current_user_id",
        lambda: user_id,
    )

    monkeypatch.setattr(
        budget_service,
        "get_current_user_id",
        lambda: user_id,
    )

    monkeypatch.setattr(
        friend_money_service,
        "get_current_user_id",
        lambda: user_id,
    )

    monkeypatch.setattr(
        savings_service,
        "get_current_user_id",
        lambda: user_id,
    )

    monkeypatch.setattr(
        recurring_service,
        "get_current_user_id",
        lambda: user_id,
    )

    monkeypatch.setattr(
        backup_service,
        "get_current_user_id",
        lambda: user_id,
    )

    # -----------------------------------------------------
    # Make the test user available to individual tests
    # if a future test needs it.
    # -----------------------------------------------------

    return user