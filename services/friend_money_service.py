from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.transaction_service import create_transaction
from utils.validators import validate_amount


def _decimal(value) -> Decimal:
    """Convert a value safely to Decimal."""
    return Decimal(str(value or "0.00"))


def get_all_people() -> list[dict]:
    """Return all people."""
    response = (
        get_table("people")
        .select("*")
        .order("name")
        .execute()
    )

    return response.data or []


def get_person(person_id: str) -> dict | None:
    """Return one person."""
    response = (
        get_table("people")
        .select("*")
        .eq("id", person_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_person(
    name: str,
    notes: str | None = None,
) -> dict:
    """Create a person."""

    name = name.strip()

    if not name:
        raise ValueError("Person name is required.")

    existing = (
        get_table("people")
        .select("id")
        .eq("name", name)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise ValueError(
            f"Person '{name}' already exists."
        )

    response = (
        get_table("people")
        .insert(
            {
                "name": name,
                "notes": notes.strip() if notes else None,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError("Person could not be created.")

    return response.data[0]


def record_money_received(
    person_id: str,
    account_id: str,
    amount,
    received_date: date,
    expected_return_date: date | None = None,
    notes: str | None = None,
) -> dict:
    """
    Record money received from a friend.

    This increases the bank account balance but is NOT personal income.
    """

    amount = validate_amount(amount)

    person = get_person(person_id)

    if person is None:
        raise ValueError("Person not found.")

    transaction = create_transaction(
        transaction_date=received_date,
        transaction_type="friend_money_received",
        amount=amount,
        source_account_id=account_id,
        person_id=person_id,
        description=f"Money received from {person['name']}",
        notes=notes,
    )

    response = (
        get_table("friends_money")
        .insert(
            {
                "person_id": person_id,
                "transaction_id": transaction["id"],
                "account_id": account_id,
                "amount_received": str(amount),
                "amount_returned": "0.00",
                "received_date": received_date.isoformat(),
                "expected_return_date": (
                    expected_return_date.isoformat()
                    if expected_return_date
                    else None
                ),
                "status": "holding",
                "notes": notes.strip() if notes else None,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Friend money record could not be created."
        )

    return response.data[0]


def get_friend_money_records() -> list[dict]:
    """Return all friend-money records."""
    response = (
        get_table("friends_money")
        .select("*")
        .order("received_date", desc=True)
        .execute()
    )

    return response.data or []


def get_total_friend_money_held() -> Decimal:
    """Return the total outstanding friend money."""

    records = get_friend_money_records()

    total = Decimal("0.00")

    for record in records:
        total += (
            _decimal(record.get("amount_received"))
            - _decimal(record.get("amount_returned"))
        )

    return total.quantize(Decimal("0.01"))


def record_money_returned(
    friend_money_id: str,
    amount,
    return_date: date,
    notes: str | None = None,
) -> dict:
    """
    Record money returned to a friend.
    """

    amount = validate_amount(amount)

    response = (
        get_table("friends_money")
        .select("*")
        .eq("id", friend_money_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Friend money record not found."
        )

    record = response.data[0]

    received = _decimal(
        record.get("amount_received")
    )

    already_returned = _decimal(
        record.get("amount_returned")
    )

    outstanding = received - already_returned

    if amount > outstanding:
        raise ValueError(
            "Return amount cannot exceed outstanding friend money."
        )

    person = get_person(record["person_id"])

    if person is None:
        raise ValueError("Person not found.")

    transaction = create_transaction(
        transaction_date=return_date,
        transaction_type="friend_money_returned",
        amount=amount,
        source_account_id=record["account_id"],
        person_id=record["person_id"],
        description=f"Money returned to {person['name']}",
        notes=notes,
    )

    new_returned = already_returned + amount

    if new_returned == received:
        status = "fully_returned"
    else:
        status = "partially_returned"

    updated = (
        get_table("friends_money")
        .update(
            {
                "amount_returned": str(new_returned),
                "status": status,
                "notes": notes.strip()
                if notes
                else record.get("notes"),
            }
        )
        .eq("id", friend_money_id)
        .execute()
    )

    if not updated.data:
        raise RuntimeError(
            "Friend money record could not be updated."
        )

    return updated.data[0]

def update_friend_money(
    friend_money_id: str,
    updates: dict,
) -> dict:
    """
    Update a friend-money record.

    Keeps the linked received transaction synchronized when
    transaction-level fields are changed.
    """

    if not updates:
        raise ValueError("No changes were provided.")

    response = (
        get_table("friends_money")
        .select("*")
        .eq("id", friend_money_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Friend money record not found."
        )

    record = response.data[0]

    allowed_fields = {
        "expected_return_date",
        "notes",
    }

    friend_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    if "expected_return_date" in friend_updates:
        value = friend_updates["expected_return_date"]
        friend_updates["expected_return_date"] = (
            value.isoformat() if value else None
        )

    if "notes" in friend_updates:
        friend_updates["notes"] = (
            friend_updates["notes"].strip()
            if friend_updates["notes"]
            else None
        )

    if friend_updates:
        updated = (
            get_table("friends_money")
            .update(friend_updates)
            .eq("id", friend_money_id)
            .execute()
        )

        if not updated.data:
            raise RuntimeError(
                "Friend money record could not be updated."
            )

    # Keep the linked received transaction's notes synchronized.
    if "notes" in updates:
        (
            get_table("transactions")
            .update(
                {
                    "notes": (
                        updates["notes"].strip()
                        if updates["notes"]
                        else None
                    )
                }
            )
            .eq("id", record["transaction_id"])
            .execute()
        )

    final_response = (
        get_table("friends_money")
        .select("*")
        .eq("id", friend_money_id)
        .limit(1)
        .execute()
    )

    if not final_response.data:
        raise RuntimeError(
            "Friend money record could not be retrieved."
        )

    return final_response.data[0]