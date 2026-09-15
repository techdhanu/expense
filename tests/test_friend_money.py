from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.account_service import ensure_default_accounts, get_all_accounts
from services.friend_money_service import (
    create_person,
    record_money_received,
    record_money_returned,
    get_total_friend_money_held,
)


def test_friend_money_received():
    ensure_default_accounts()

    accounts = get_all_accounts()
    account = next(a for a in accounts if a["name"] == "General Account")

    person = create_person("TEST FRIEND AUTOMATED")

    record = record_money_received(
        person_id=person["id"],
        account_id=account["id"],
        amount=5000,
        received_date=date.today(),
        notes="Automated test",
    )

    assert Decimal(str(record["amount_received"])) == Decimal("5000.00")
    assert get_total_friend_money_held() == Decimal("5000.00")

    # Cleanup
    get_table("friends_money").delete().eq("id", record["id"]).execute()
    get_table("transactions").delete().eq(
        "id", record["transaction_id"]
    ).execute()
    get_table("people").delete().eq("id", person["id"]).execute()


def test_friend_money_returned():
    ensure_default_accounts()

    accounts = get_all_accounts()
    account = next(a for a in accounts if a["name"] == "General Account")

    person = create_person("TEST FRIEND RETURN AUTOMATED")

    received = record_money_received(
        person_id=person["id"],
        account_id=account["id"],
        amount=5000,
        received_date=date.today(),
    )

    returned = record_money_returned(
        friend_money_id=received["id"],
        amount=2000,
        return_date=date.today(),
    )

    assert Decimal(str(returned["amount_returned"])) == Decimal("2000.00")
    assert get_total_friend_money_held() == Decimal("3000.00")

    # Find the return transaction created by the service
    return_transactions = (
        get_table("transactions")
        .select("*")
        .eq("person_id", person["id"])
        .eq("transaction_type", "friend_money_returned")
        .execute()
        .data
    )

    assert len(return_transactions) == 1

    # Cleanup
    get_table("friends_money").delete().eq("id", received["id"]).execute()
    get_table("transactions").delete().eq(
        "id", received["transaction_id"]
    ).execute()

    for transaction in return_transactions:
        get_table("transactions").delete().eq(
            "id", transaction["id"]
        ).execute()

    get_table("people").delete().eq("id", person["id"]).execute()