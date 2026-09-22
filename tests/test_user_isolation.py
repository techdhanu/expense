from datetime import date
from decimal import Decimal

import pytest

from database.queries import get_table
from services.account_service import (
    create_account,
    get_account,
    get_all_accounts,
)
from services.category_service import (
    create_category,
    get_all_categories,
)
from services.transaction_service import (
    create_expense,
    get_all_transactions,
    get_transaction,
    update_transaction,
    delete_transaction,
)
from services.budget_service import (
    create_budget,
    get_all_budgets,
    update_budget,
)
from services.savings_service import (
    create_savings_goal,
    get_all_savings_goals,
    update_savings_goal,
)
from services.friend_money_service import (
    create_person,
    get_all_people,
)
from services.authentication_service import (
    authenticate_user,
    create_user,
)


TEST_USER_A = "pytest_isolation_a"
TEST_USER_B = "pytest_isolation_b"
TEST_PASSWORD = "IsolationPassword123!"


def get_or_create_user(username):
    user = authenticate_user(username, TEST_PASSWORD)

    if user is None:
        user = create_user(username, TEST_PASSWORD)

    assert user is not None

    return user


@pytest.fixture
def two_users(monkeypatch):
    user_a = get_or_create_user(TEST_USER_A)
    user_b = get_or_create_user(TEST_USER_B)

    user_a_id = str(user_a["id"])
    user_b_id = str(user_b["id"])

    import services.account_service as account_service
    import services.transaction_service as transaction_service
    import services.category_service as category_service
    import services.budget_service as budget_service
    import services.savings_service as savings_service
    import services.friend_money_service as friend_money_service

    def switch_user(user_id):
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
            savings_service,
            "get_current_user_id",
            lambda: user_id,
        )

        monkeypatch.setattr(
            friend_money_service,
            "get_current_user_id",
            lambda: user_id,
        )

    return user_a_id, user_b_id, switch_user


def test_accounts_are_isolated(two_users):
    user_a_id, user_b_id, switch_user = two_users

    switch_user(user_a_id)

    account_a = create_account(
        name="ISOLATION ACCOUNT A",
        account_type="bank",
        opening_balance=Decimal("5000.00"),
    )

    try:
        accounts_a = get_all_accounts()

        assert any(
            account["id"] == account_a["id"]
            for account in accounts_a
        )

        switch_user(user_b_id)

        accounts_b = get_all_accounts()

        assert not any(
            account["id"] == account_a["id"]
            for account in accounts_b
        )

        assert get_account(account_a["id"]) is None

    finally:
        switch_user(user_a_id)

        get_table("accounts").delete().eq(
            "id",
            account_a["id"],
        ).execute()


def test_categories_are_isolated(two_users):
    user_a_id, user_b_id, switch_user = two_users

    switch_user(user_a_id)

    category_a = create_category(
        name="ISOLATION CATEGORY A",
        category_type="expense",
    )

    try:
        categories_a = get_all_categories()

        assert any(
            category["id"] == category_a["id"]
            for category in categories_a
        )

        switch_user(user_b_id)

        categories_b = get_all_categories()

        assert not any(
            category["id"] == category_a["id"]
            for category in categories_b
        )

    finally:
        switch_user(user_a_id)

        get_table("categories").delete().eq(
            "id",
            category_a["id"],
        ).execute()


def test_transactions_are_isolated(two_users):
    user_a_id, user_b_id, switch_user = two_users

    switch_user(user_a_id)

    account_a = create_account(
        name="ISOLATION TX ACCOUNT A",
        account_type="bank",
        opening_balance=Decimal("5000.00"),
    )

    category_a = create_category(
        name="ISOLATION TX CATEGORY A",
        category_type="expense",
    )

    transaction_a = create_expense(
        transaction_date=date.today(),
        amount=Decimal("250.00"),
        account_id=account_a["id"],
        category_id=category_a["id"],
        description="USER A PRIVATE TRANSACTION",
    )

    try:
        transactions_a = get_all_transactions()

        assert any(
            transaction["id"] == transaction_a["id"]
            for transaction in transactions_a
        )

        switch_user(user_b_id)

        transactions_b = get_all_transactions()

        assert not any(
            transaction["id"] == transaction_a["id"]
            for transaction in transactions_b
        )

        assert get_transaction(transaction_a["id"]) is None

    finally:
        switch_user(user_a_id)

        delete_transaction(transaction_a["id"])

        get_table("categories").delete().eq(
            "id",
            category_a["id"],
        ).execute()

        get_table("accounts").delete().eq(
            "id",
            account_a["id"],
        ).execute()


def test_user_cannot_update_another_users_transaction(two_users):
    user_a_id, user_b_id, switch_user = two_users

    switch_user(user_a_id)

    account_a = create_account(
        name="ISOLATION UPDATE ACCOUNT A",
        account_type="bank",
        opening_balance=Decimal("5000.00"),
    )

    category_a = create_category(
        name="ISOLATION UPDATE CATEGORY A",
        category_type="expense",
    )

    transaction_a = create_expense(
        transaction_date=date.today(),
        amount=Decimal("300.00"),
        account_id=account_a["id"],
        category_id=category_a["id"],
        description="PRIVATE UPDATE TEST",
    )

    try:
        switch_user(user_b_id)

        with pytest.raises(
            (ValueError, RuntimeError),
        ):
            update_transaction(
                transaction_a["id"],
                {
                    "description": "USER B ATTEMPT",
                },
            )

        switch_user(user_a_id)

        transaction_after = get_transaction(
            transaction_a["id"]
        )

        assert transaction_after is not None
        assert transaction_after["description"] == "PRIVATE UPDATE TEST"

    finally:
        switch_user(user_a_id)

        delete_transaction(transaction_a["id"])

        get_table("categories").delete().eq(
            "id",
            category_a["id"],
        ).execute()

        get_table("accounts").delete().eq(
            "id",
            account_a["id"],
        ).execute()

def test_user_cannot_delete_another_users_transaction(two_users):
    user_a_id, user_b_id, switch_user = two_users

    switch_user(user_a_id)

    account_a = create_account(
        name="ISOLATION DELETE ACCOUNT A",
        account_type="bank",
        opening_balance=Decimal("5000.00"),
    )

    category_a = create_category(
        name="ISOLATION DELETE CATEGORY A",
        category_type="expense",
    )

    transaction_a = create_expense(
        transaction_date=date.today(),
        amount=Decimal("200.00"),
        account_id=account_a["id"],
        category_id=category_a["id"],
        description="PRIVATE DELETE TEST",
    )

    try:
        switch_user(user_b_id)

        with pytest.raises(
            (ValueError, RuntimeError),
        ):
            delete_transaction(transaction_a["id"])

        switch_user(user_a_id)

        assert get_transaction(
            transaction_a["id"]
        ) is not None

    finally:
        switch_user(user_a_id)

        delete_transaction(transaction_a["id"])

        get_table("categories").delete().eq(
            "id",
            category_a["id"],
        ).execute()

        get_table("accounts").delete().eq(
            "id",
            account_a["id"],
        ).execute()


def test_budgets_are_isolated(two_users):
    user_a_id, user_b_id, switch_user = two_users

    switch_user(user_a_id)

    category_a = create_category(
        name="ISOLATION BUDGET CATEGORY A",
        category_type="expense",
    )

    budget_a = create_budget(
        category_id=category_a["id"],
        month=date.today().month,
        year=date.today().year,
        amount=Decimal("5000.00"),
    )

    try:
        switch_user(user_b_id)

        budgets_b = get_all_budgets()

        assert not any(
            budget["id"] == budget_a["id"]
            for budget in budgets_b
        )

    finally:
        switch_user(user_a_id)

        get_table("budgets").delete().eq(
            "id",
            budget_a["id"],
        ).execute()

        get_table("categories").delete().eq(
            "id",
            category_a["id"],
        ).execute()


def test_savings_goals_are_isolated(two_users):
    user_a_id, user_b_id, switch_user = two_users

    switch_user(user_a_id)

    goal_a = create_savings_goal(
        name="ISOLATION SAVINGS GOAL A",
        target_amount=Decimal("10000.00"),
        target_date=date.today(),
    )

    try:
        switch_user(user_b_id)

        goals_b = get_all_savings_goals()

        assert not any(
            goal["id"] == goal_a["id"]
            for goal in goals_b
        )

    finally:
        switch_user(user_a_id)

        get_table("savings_goals").delete().eq(
            "id",
            goal_a["id"],
        ).execute()


def test_people_are_isolated(two_users):
    user_a_id, user_b_id, switch_user = two_users

    switch_user(user_a_id)

    person_a = create_person(
        name="ISOLATION PERSON A",
    )

    try:
        people_a = get_all_people()

        assert any(
            person["id"] == person_a["id"]
            for person in people_a
        )

        switch_user(user_b_id)

        people_b = get_all_people()

        assert not any(
            person["id"] == person_a["id"]
            for person in people_b
        )

    finally:
        switch_user(user_a_id)

        get_table("people").delete().eq(
            "id",
            person_a["id"],
        ).execute()