from datetime import date
from decimal import Decimal

from database.queries import get_table
from services.transaction_service import create_transaction
from utils.validators import validate_amount


def _decimal(value) -> Decimal:
    """Convert a value safely to Decimal."""
    return Decimal(str(value or "0.00"))


# ============================================================
# PEOPLE
# ============================================================

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


# ============================================================
# FRIEND MONEY RECEIVED
# ============================================================

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
                "notes": (
                    notes.strip()
                    if notes
                    else record.get("notes")
                ),
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


# ============================================================
# MONEY LENT / RECEIVABLE
# ============================================================

def record_money_lent(
    person_id: str,
    account_id: str,
    amount,
    lent_date: date,
    expected_return_date: date | None = None,
    notes: str | None = None,
) -> dict:
    """
    Record money lent to a friend.

    This decreases the account balance but is NOT an expense.
    The amount becomes a receivable from the friend.
    """

    amount = validate_amount(amount)

    person = get_person(person_id)

    if person is None:
        raise ValueError("Person not found.")

    transaction = create_transaction(
        transaction_date=lent_date,
        transaction_type="friend_money_lent",
        amount=amount,
        source_account_id=account_id,
        person_id=person_id,
        description=f"Money lent to {person['name']}",
        notes=notes,
    )

    response = (
        get_table("money_lent")
        .insert(
            {
                "person_id": person_id,
                "transaction_id": transaction["id"],
                "account_id": account_id,
                "amount_lent": str(amount),
                "amount_returned": "0.00",
                "lent_date": lent_date.isoformat(),
                "expected_return_date": (
                    expected_return_date.isoformat()
                    if expected_return_date
                    else None
                ),
                "status": "lent",
                "notes": notes.strip() if notes else None,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Money lent record could not be created."
        )

    return response.data[0]


def get_money_lent_records() -> list[dict]:
    """Return all money-lent records."""

    response = (
        get_table("money_lent")
        .select("*")
        .order("lent_date", desc=True)
        .execute()
    )

    return response.data or []


def get_total_money_lent_outstanding() -> Decimal:
    """Return the total amount currently owed to the user."""

    records = get_money_lent_records()

    total = Decimal("0.00")

    for record in records:
        total += (
            _decimal(record.get("amount_lent"))
            - _decimal(record.get("amount_returned"))
        )

    return total.quantize(Decimal("0.01"))


def record_money_lent_returned(
    money_lent_id: str,
    amount,
    return_date: date,
    notes: str | None = None,
) -> dict:
    """
    Record money returned by a friend.

    This increases the user's account balance but is NOT income.
    """

    amount = validate_amount(amount)

    response = (
        get_table("money_lent")
        .select("*")
        .eq("id", money_lent_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Money lent record not found."
        )

    record = response.data[0]

    amount_lent = _decimal(
        record.get("amount_lent")
    )

    already_returned = _decimal(
        record.get("amount_returned")
    )

    outstanding = amount_lent - already_returned

    if outstanding <= Decimal("0.00"):
        raise ValueError(
            "This money-lent record has already been fully returned."
        )

    if amount > outstanding:
        raise ValueError(
            "Return amount cannot exceed outstanding lent money."
        )

    person = get_person(record["person_id"])

    if person is None:
        raise ValueError("Person not found.")

    transaction = create_transaction(
        transaction_date=return_date,
        transaction_type="friend_money_lent_returned",
        amount=amount,
        source_account_id=record["account_id"],
        person_id=record["person_id"],
        description=f"Money received back from {person['name']}",
        notes=notes,
    )

    new_returned = already_returned + amount

    if new_returned == amount_lent:
        status = "fully_returned"
    else:
        status = "partially_returned"

    updated = (
        get_table("money_lent")
        .update(
            {
                "amount_returned": str(new_returned),
                "status": status,
                "notes": (
                    notes.strip()
                    if notes
                    else record.get("notes")
                ),
            }
        )
        .eq("id", money_lent_id)
        .execute()
    )

    if not updated.data:
        raise RuntimeError(
            "Money lent record could not be updated."
        )

    return updated.data[0]


def update_money_lent(
    money_lent_id: str,
    updates: dict,
) -> dict:
    """
    Update editable details of a money-lent record.

    Financial amounts and return values are intentionally
    not editable here.
    """

    if not updates:
        raise ValueError("No changes were provided.")

    response = (
        get_table("money_lent")
        .select("*")
        .eq("id", money_lent_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Money lent record not found."
        )

    record = response.data[0]

    allowed_fields = {
        "expected_return_date",
        "notes",
    }

    lent_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    if "expected_return_date" in lent_updates:
        value = lent_updates["expected_return_date"]

        lent_updates["expected_return_date"] = (
            value.isoformat() if value else None
        )

    if "notes" in lent_updates:
        lent_updates["notes"] = (
            lent_updates["notes"].strip()
            if lent_updates["notes"]
            else None
        )

    if lent_updates:
        updated = (
            get_table("money_lent")
            .update(lent_updates)
            .eq("id", money_lent_id)
            .execute()
        )

        if not updated.data:
            raise RuntimeError(
                "Money lent record could not be updated."
            )

    # Keep the linked lending transaction's notes synchronized.
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
        get_table("money_lent")
        .select("*")
        .eq("id", money_lent_id)
        .limit(1)
        .execute()
    )

    if not final_response.data:
        raise RuntimeError(
            "Money lent record could not be retrieved."
        )

    return final_response.data[0]