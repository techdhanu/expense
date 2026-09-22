import uuid
from datetime import date

import services.account_service as account_service
import services.friend_money_service as friend_money_service


def _test_person_name(prefix: str) -> str:
    """Generate a unique person name for each test run."""
    return f"{prefix} {uuid.uuid4().hex[:8]}"


def _get_test_account_id() -> str:
    """Get an active account belonging to the current test user."""
    accounts = account_service.get_all_accounts()

    assert accounts, "No active account available for the test user."

    return accounts[0]["id"]


def _cleanup_person(person_id: str) -> None:
    """
    Clean up all records created for the test person.

    Transactions must be deleted before the person because transactions
    reference the person through a foreign key.
    """
    user_id = friend_money_service.get_current_user_id()
    client = friend_money_service.get_supabase_client()

    # Delete friend-money records first.
    client.table("friends_money") \
        .delete() \
        .eq("user_id", user_id) \
        .eq("person_id", person_id) \
        .execute()

    # Delete money-lent records.
    client.table("money_lent") \
        .delete() \
        .eq("user_id", user_id) \
        .eq("person_id", person_id) \
        .execute()

    # Find transactions linked to this person.
    transactions_response = (
        client.table("transactions")
        .select("id")
        .eq("user_id", user_id)
        .eq("person_id", person_id)
        .execute()
    )

    transaction_ids = [
        row["id"]
        for row in (transactions_response.data or [])
    ]

    # Delete linked transactions.
    if transaction_ids:
        (
            client.table("transactions")
            .delete()
            .eq("user_id", user_id)
            .in_("id", transaction_ids)
            .execute()
        )

    # Finally delete the person.
    (
        client.table("people")
        .delete()
        .eq("user_id", user_id)
        .eq("id", person_id)
        .execute()
    )


def test_friend_money_received():
    """Test recording money received from a friend."""
    person_id = None

    try:
        account_id = _get_test_account_id()

        person = friend_money_service.create_person(
            _test_person_name("TEST FRIEND AUTOMATED")
        )

        person_id = person["id"]

        result = friend_money_service.record_money_received(
            person_id=person_id,
            account_id=account_id,
            amount="1000",
            received_date=date(2026, 9, 15),
            expected_return_date=date(2026, 9, 30),
            notes="Automated test",
        )

        assert result is not None
        assert result["person_id"] == person_id
        assert result["account_id"] == account_id
        assert result["amount_received"] == 1000

    finally:
        if person_id:
            _cleanup_person(person_id)


def test_friend_money_returned():
    """Test returning money received from a friend."""
    person_id = None

    try:
        account_id = _get_test_account_id()

        person = friend_money_service.create_person(
            _test_person_name("TEST FRIEND RETURN AUTOMATED")
        )

        person_id = person["id"]

        received = friend_money_service.record_money_received(
            person_id=person_id,
            account_id=account_id,
            amount="1000",
            received_date=date(2026, 9, 15),
            expected_return_date=date(2026, 9, 30),
            notes="Return test",
        )

        friend_money_id = received["id"]

        result = friend_money_service.record_money_returned(
            friend_money_id=friend_money_id,
            amount="400",
            return_date=date(2026, 9, 16),
            notes="Partial return",
        )

        assert result is not None
        assert result["id"] == friend_money_id
        assert result["amount_returned"] == 400
        assert result["status"] == "partially_returned"

    finally:
        if person_id:
            _cleanup_person(person_id)


def test_money_lent():
    """Test recording money lent to a friend."""
    person_id = None

    try:
        account_id = _get_test_account_id()

        person = friend_money_service.create_person(
            _test_person_name("TEST MONEY LENT AUTOMATED")
        )

        person_id = person["id"]

        result = friend_money_service.record_money_lent(
            person_id=person_id,
            account_id=account_id,
            amount="1500",
            lent_date=date(2026, 9, 15),
            expected_return_date=date(2026, 9, 30),
            notes="Automated lent test",
        )

        assert result is not None
        assert result["person_id"] == person_id
        assert result["account_id"] == account_id
        assert result["amount_lent"] == 1500

    finally:
        if person_id:
            _cleanup_person(person_id)


def test_money_lent_returned():
    """Test receiving repayment for money previously lent."""
    person_id = None

    try:
        account_id = _get_test_account_id()

        person = friend_money_service.create_person(
            _test_person_name("TEST MONEY LENT RETURN AUTOMATED")
        )

        person_id = person["id"]

        lent = friend_money_service.record_money_lent(
            person_id=person_id,
            account_id=account_id,
            amount="1500",
            lent_date=date(2026, 9, 15),
            expected_return_date=date(2026, 9, 30),
            notes="Lent return test",
        )

        money_lent_id = lent["id"]

        result = friend_money_service.record_money_lent_returned(
            money_lent_id=money_lent_id,
            amount="500",
            return_date=date(2026, 9, 16),
            notes="Partial repayment",
        )

        assert result is not None
        assert result["id"] == money_lent_id
        assert result["amount_returned"] == 500
        assert result["status"] == "partially_returned"

    finally:
        if person_id:
            _cleanup_person(person_id)


def test_friend_money_cannot_return_more_than_outstanding():
    """
    Verify the database atomic RPC rejects a return amount greater
    than the outstanding friend money.

    The validation happens inside PostgreSQL, so Supabase/PostgREST
    raises APIError rather than Python ValueError.
    """
    person_id = None

    try:
        account_id = _get_test_account_id()

        person = friend_money_service.create_person(
            _test_person_name("TEST FRIEND OVERRETURN AUTOMATED")
        )

        person_id = person["id"]

        received = friend_money_service.record_money_received(
            person_id=person_id,
            account_id=account_id,
            amount="1000",
            received_date=date(2026, 9, 15),
            expected_return_date=date(2026, 9, 30),
            notes="Over-return test",
        )

        friend_money_id = received["id"]

        try:
            friend_money_service.record_money_returned(
                friend_money_id=friend_money_id,
                amount="1001",
                return_date=date(2026, 9, 16),
                notes="Should fail",
            )

            assert False, (
                "Expected over-return to fail, "
                "but the operation succeeded."
            )

        except Exception as exc:
            assert (
                "Return amount cannot exceed outstanding friend money."
                in str(exc)
            )

    finally:
        if person_id:
            _cleanup_person(person_id)


def test_money_lent_cannot_return_more_than_outstanding():
    """
    Verify the database atomic RPC rejects a repayment amount
    greater than the outstanding lent money.

    The validation happens inside PostgreSQL, so Supabase/PostgREST
    raises APIError rather than Python ValueError.
    """
    person_id = None

    try:
        account_id = _get_test_account_id()

        person = friend_money_service.create_person(
            _test_person_name("TEST MONEY LENT OVERRETURN AUTOMATED")
        )

        person_id = person["id"]

        lent = friend_money_service.record_money_lent(
            person_id=person_id,
            account_id=account_id,
            amount="1000",
            lent_date=date(2026, 9, 15),
            expected_return_date=date(2026, 9, 30),
            notes="Over-return test",
        )

        money_lent_id = lent["id"]

        try:
            friend_money_service.record_money_lent_returned(
                money_lent_id=money_lent_id,
                amount="1001",
                return_date=date(2026, 9, 16),
                notes="Should fail",
            )

            assert False, (
                "Expected over-return to fail, "
                "but the operation succeeded."
            )

        except Exception as exc:
            assert (
                "Return amount cannot exceed outstanding lent money."
                in str(exc)
            )

    finally:
        if person_id:
            _cleanup_person(person_id)