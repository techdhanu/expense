from datetime import date
from decimal import Decimal, InvalidOperation

from database.queries import get_table
from database.client import get_supabase_client
from services.authentication_service import get_current_user_id
from utils.validators import validate_amount


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _decimal(value) -> Decimal:
    """Convert a database or application value safely to Decimal."""

    try:
        if value is None or value == "":
            return Decimal("0.00")

        result = Decimal(str(value))

        if not result.is_finite():
            raise ValueError("Financial amount must be finite.")

        return result

    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            "Invalid financial amount."
        ) from exc


def _get_owned_person(person_id: str) -> dict:
    """
    Return a person belonging to the currently logged-in user.
    """

    if not person_id:
        raise ValueError("Person ID is required.")

    user_id = get_current_user_id()

    response = (
        get_table("people")
        .select("*")
        .eq("id", person_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Person not found or does not belong to the current user."
        )

    return response.data[0]


def _validate_owned_account(account_id: str) -> dict:
    """
    Return an active account belonging to the current user.
    """

    if not account_id:
        raise ValueError("Account ID is required.")

    user_id = get_current_user_id()

    response = (
        get_table("accounts")
        .select("*")
        .eq("id", account_id)
        .eq("user_id", user_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Account not found or does not belong to the current user."
        )

    return response.data[0]


def _rpc_result(response):
    """
    Normalize Supabase RPC response data.

    PostgreSQL functions return a JSON object, which the
    Supabase Python client normally exposes as a dict.
    """

    data = getattr(response, "data", None)

    if isinstance(data, dict):
        return data

    if isinstance(data, list) and data:
        if isinstance(data[0], dict):
            return data[0]

    raise RuntimeError(
        "The database operation did not return a valid result."
    )


# ============================================================
# PEOPLE
# ============================================================

def get_all_people() -> list[dict]:
    """Return all people belonging to the current user."""

    user_id = get_current_user_id()

    response = (
        get_table("people")
        .select("*")
        .eq("user_id", user_id)
        .order("name")
        .execute()
    )

    return response.data or []


def get_person(person_id: str) -> dict | None:
    """
    Return one person belonging to the current user.
    """

    if not person_id:
        raise ValueError("Person ID is required.")

    user_id = get_current_user_id()

    response = (
        get_table("people")
        .select("*")
        .eq("id", person_id)
        .eq("user_id", user_id)
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
    """Create a person for the current user."""

    user_id = get_current_user_id()

    if not name:
        raise ValueError("Person name is required.")

    name = name.strip()

    if not name:
        raise ValueError("Person name is required.")

    if len(name) > 100:
        raise ValueError(
            "Person name cannot exceed 100 characters."
        )

    if notes is not None:
        notes = notes.strip()

        if len(notes) > 500:
            raise ValueError(
                "Person notes cannot exceed 500 characters."
            )

    # --------------------------------------------------------
    # Duplicate check is user-scoped
    # --------------------------------------------------------

    existing = (
        get_table("people")
        .select("id")
        .eq("user_id", user_id)
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
                "user_id": user_id,
                "name": name,
                "notes": notes or None,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Person could not be created."
        )

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

    This increases the bank account balance but is NOT
    personal income.

    The transaction and friend-money liability record are
    created atomically inside PostgreSQL.
    """

    # --------------------------------------------------------
    # Validate ownership before calling the RPC
    # --------------------------------------------------------

    person = _get_owned_person(person_id)

    _validate_owned_account(account_id)

    # --------------------------------------------------------
    # Validate amount
    # --------------------------------------------------------

    amount = validate_amount(amount)

    # --------------------------------------------------------
    # Validate dates
    # --------------------------------------------------------

    if not isinstance(received_date, date):
        raise ValueError(
            "Received date is invalid."
        )

    if (
        expected_return_date is not None
        and not isinstance(expected_return_date, date)
    ):
        raise ValueError(
            "Expected return date is invalid."
        )

    if (
        expected_return_date is not None
        and expected_return_date < received_date
    ):
        raise ValueError(
            "Expected return date cannot be before received date."
        )

    # --------------------------------------------------------
    # Validate notes
    # --------------------------------------------------------

    if notes is not None:
        notes = notes.strip()

        if len(notes) > 500:
            raise ValueError(
                "Notes cannot exceed 500 characters."
            )

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Atomic PostgreSQL operation
    # --------------------------------------------------------

    response = get_supabase_client().rpc(
        "record_friend_money_received_atomic",
        {
            "p_person_id": person_id,
            "p_account_id": account_id,
            "p_amount": str(amount),
            "p_received_date": received_date.isoformat(),
            "p_expected_return_date": (
                expected_return_date.isoformat()
                if expected_return_date
                else None
            ),
            "p_notes": notes,
            "p_user_id": user_id,
        },
    ).execute()

    result = _rpc_result(response)

    # --------------------------------------------------------
    # Ensure returned person still belongs to current user
    # --------------------------------------------------------

    if result.get("person_id") != person_id:
        raise RuntimeError(
            "Database returned an unexpected person."
        )

    if result.get("account_id") != account_id:
        raise RuntimeError(
            "Database returned an unexpected account."
        )

    return result


# ============================================================
# FRIEND MONEY RECORDS
# ============================================================

def get_friend_money_records() -> list[dict]:
    """Return all friend-money records for the current user."""

    user_id = get_current_user_id()

    response = (
        get_table("friends_money")
        .select("*")
        .eq("user_id", user_id)
        .order("received_date", desc=True)
        .execute()
    )

    return response.data or []


def get_total_friend_money_held() -> Decimal:
    """Return the total outstanding friend money for the current user."""

    records = get_friend_money_records()

    total = Decimal("0.00")

    for record in records:

        received = _decimal(
            record.get("amount_received")
        )

        returned = _decimal(
            record.get("amount_returned")
        )

        outstanding = received - returned

        if outstanding > Decimal("0.00"):
            total += outstanding

    return total.quantize(
        Decimal("0.01")
    )


# ============================================================
# FRIEND MONEY RETURNED
# ============================================================

def record_money_returned(
    friend_money_id: str,
    amount,
    return_date: date,
    notes: str | None = None,
) -> dict:
    """
    Record money returned to a friend.

    The return transaction and liability update are performed
    atomically inside PostgreSQL.
    """

    amount = validate_amount(amount)

    user_id = get_current_user_id()

    if not isinstance(return_date, date):
        raise ValueError(
            "Return date is invalid."
        )

    if notes is not None:
        notes = notes.strip()

        if len(notes) > 500:
            raise ValueError(
                "Notes cannot exceed 500 characters."
            )

    # --------------------------------------------------------
    # Verify record belongs to current user before RPC
    # --------------------------------------------------------

    response = (
        get_table("friends_money")
        .select("id,user_id")
        .eq("id", friend_money_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Friend money record not found."
        )

    # --------------------------------------------------------
    # Atomic PostgreSQL operation
    # --------------------------------------------------------

    rpc_response = get_supabase_client().rpc(
        "record_friend_money_returned_atomic",
        {
            "p_friend_money_id": friend_money_id,
            "p_amount": str(amount),
            "p_return_date": return_date.isoformat(),
            "p_notes": notes,
            "p_user_id": user_id,
        },
    ).execute()

    result = _rpc_result(rpc_response)

    if result.get("id") != friend_money_id:
        raise RuntimeError(
            "Database returned an unexpected friend-money record."
        )

    return result


# ============================================================
# FRIEND MONEY UPDATE
# ============================================================

def update_friend_money(
    friend_money_id: str,
    updates: dict,
) -> dict:
    """
    Update editable non-financial fields.

    Financial amounts and return amounts are intentionally
    not editable.
    """

    if not updates:
        raise ValueError(
            "No changes were provided."
        )

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Get current user's record
    # --------------------------------------------------------

    response = (
        get_table("friends_money")
        .select("*")
        .eq("id", friend_money_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Friend money record not found."
        )

    record = response.data[0]

    # --------------------------------------------------------
    # Allowed fields
    # --------------------------------------------------------

    allowed_fields = {
        "expected_return_date",
        "notes",
    }

    unexpected_fields = (
        set(updates) - allowed_fields
    )

    if unexpected_fields:
        raise ValueError(
            "Unsupported friend-money field(s): "
            + ", ".join(
                sorted(unexpected_fields)
            )
        )

    friend_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    # --------------------------------------------------------
    # Validate expected return date
    # --------------------------------------------------------

    if "expected_return_date" in friend_updates:

        value = friend_updates[
            "expected_return_date"
        ]

        if value is not None and not isinstance(value, date):
            raise ValueError(
                "Expected return date is invalid."
            )

        received_date = record.get(
            "received_date"
        )

        if (
            value is not None
            and received_date
            and value.isoformat() < str(received_date)
        ):
            raise ValueError(
                "Expected return date cannot be before received date."
            )

        friend_updates[
            "expected_return_date"
        ] = (
            value.isoformat()
            if value
            else None
        )

    # --------------------------------------------------------
    # Validate notes
    # --------------------------------------------------------

    if "notes" in friend_updates:

        notes = friend_updates["notes"]

        if notes is not None:

            notes = notes.strip()

            if len(notes) > 500:
                raise ValueError(
                    "Notes cannot exceed 500 characters."
                )

        friend_updates["notes"] = (
            notes or None
            if notes is not None
            else None
        )

    # --------------------------------------------------------
    # Update friend-money record
    # --------------------------------------------------------

    if friend_updates:

        updated = (
            get_table("friends_money")
            .update(friend_updates)
            .eq("id", friend_money_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not updated.data:
            raise RuntimeError(
                "Friend money record could not be updated."
            )

    # --------------------------------------------------------
    # Synchronize linked transaction notes
    #
    # This is intentionally kept user-scoped.
    # --------------------------------------------------------

    if "notes" in updates:

        transaction_update = (
            get_table("transactions")
            .update(
                {
                    "notes": friend_updates.get(
                        "notes"
                    )
                }
            )
            .eq(
                "id",
                record["transaction_id"],
            )
            .eq(
                "user_id",
                user_id,
            )
            .execute()
        )

        if not transaction_update.data:
            raise RuntimeError(
                "Linked transaction could not be updated."
            )

    # --------------------------------------------------------
    # Return final record
    # --------------------------------------------------------

    final_response = (
        get_table("friends_money")
        .select("*")
        .eq("id", friend_money_id)
        .eq("user_id", user_id)
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

    The transaction and receivable record are created
    atomically inside PostgreSQL.
    """

    # --------------------------------------------------------
    # Validate ownership
    # --------------------------------------------------------

    person = _get_owned_person(person_id)

    _validate_owned_account(account_id)

    # --------------------------------------------------------
    # Validate amount
    # --------------------------------------------------------

    amount = validate_amount(amount)

    # --------------------------------------------------------
    # Validate dates
    # --------------------------------------------------------

    if not isinstance(lent_date, date):
        raise ValueError(
            "Lent date is invalid."
        )

    if (
        expected_return_date is not None
        and not isinstance(expected_return_date, date)
    ):
        raise ValueError(
            "Expected return date is invalid."
        )

    if (
        expected_return_date is not None
        and expected_return_date < lent_date
    ):
        raise ValueError(
            "Expected return date cannot be before lent date."
        )

    # --------------------------------------------------------
    # Validate notes
    # --------------------------------------------------------

    if notes is not None:

        notes = notes.strip()

        if len(notes) > 500:
            raise ValueError(
                "Notes cannot exceed 500 characters."
            )

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Atomic PostgreSQL operation
    # --------------------------------------------------------

    response = get_supabase_client().rpc(
        "record_money_lent_atomic",
        {
            "p_person_id": person_id,
            "p_account_id": account_id,
            "p_amount": str(amount),
            "p_lent_date": lent_date.isoformat(),
            "p_expected_return_date": (
                expected_return_date.isoformat()
                if expected_return_date
                else None
            ),
            "p_notes": notes,
            "p_user_id": user_id,
        },
    ).execute()

    result = _rpc_result(response)

    if result.get("person_id") != person_id:
        raise RuntimeError(
            "Database returned an unexpected person."
        )

    if result.get("account_id") != account_id:
        raise RuntimeError(
            "Database returned an unexpected account."
        )

    return result


# ============================================================
# MONEY LENT RECORDS
# ============================================================

def get_money_lent_records() -> list[dict]:
    """Return all money-lent records for the current user."""

    user_id = get_current_user_id()

    response = (
        get_table("money_lent")
        .select("*")
        .eq("user_id", user_id)
        .order("lent_date", desc=True)
        .execute()
    )

    return response.data or []


def get_total_money_lent_outstanding() -> Decimal:
    """Return the total amount currently owed to the user."""

    records = get_money_lent_records()

    total = Decimal("0.00")

    for record in records:

        lent = _decimal(
            record.get("amount_lent")
        )

        returned = _decimal(
            record.get("amount_returned")
        )

        outstanding = lent - returned

        if outstanding > Decimal("0.00"):
            total += outstanding

    return total.quantize(
        Decimal("0.01")
    )


# ============================================================
# MONEY LENT RETURNED
# ============================================================

def record_money_lent_returned(
    money_lent_id: str,
    amount,
    return_date: date,
    notes: str | None = None,
) -> dict:
    """
    Record money returned by a friend.

    The return transaction and receivable update are performed
    atomically inside PostgreSQL.
    """

    amount = validate_amount(amount)

    user_id = get_current_user_id()

    if not isinstance(return_date, date):
        raise ValueError(
            "Return date is invalid."
        )

    if notes is not None:

        notes = notes.strip()

        if len(notes) > 500:
            raise ValueError(
                "Notes cannot exceed 500 characters."
            )

    # --------------------------------------------------------
    # Verify record belongs to current user
    # --------------------------------------------------------

    response = (
        get_table("money_lent")
        .select("id,user_id")
        .eq("id", money_lent_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Money lent record not found."
        )

    # --------------------------------------------------------
    # Atomic PostgreSQL operation
    # --------------------------------------------------------

    rpc_response = get_supabase_client().rpc(
        "record_money_lent_returned_atomic",
        {
            "p_money_lent_id": money_lent_id,
            "p_amount": str(amount),
            "p_return_date": return_date.isoformat(),
            "p_notes": notes,
            "p_user_id": user_id,
        },
    ).execute()

    result = _rpc_result(rpc_response)

    if result.get("id") != money_lent_id:
        raise RuntimeError(
            "Database returned an unexpected money-lent record."
        )

    return result


# ============================================================
# MONEY LENT UPDATE
# ============================================================

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
        raise ValueError(
            "No changes were provided."
        )

    user_id = get_current_user_id()

    # --------------------------------------------------------
    # Get current user's record
    # --------------------------------------------------------

    response = (
        get_table("money_lent")
        .select("*")
        .eq("id", money_lent_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Money lent record not found."
        )

    record = response.data[0]

    # --------------------------------------------------------
    # Allowed fields
    # --------------------------------------------------------

    allowed_fields = {
        "expected_return_date",
        "notes",
    }

    unexpected_fields = (
        set(updates) - allowed_fields
    )

    if unexpected_fields:
        raise ValueError(
            "Unsupported money-lent field(s): "
            + ", ".join(
                sorted(unexpected_fields)
            )
        )

    lent_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    # --------------------------------------------------------
    # Validate expected return date
    # --------------------------------------------------------

    if "expected_return_date" in lent_updates:

        value = lent_updates[
            "expected_return_date"
        ]

        if value is not None and not isinstance(value, date):
            raise ValueError(
                "Expected return date is invalid."
            )

        lent_date = record.get(
            "lent_date"
        )

        if (
            value is not None
            and lent_date
            and value.isoformat() < str(lent_date)
        ):
            raise ValueError(
                "Expected return date cannot be before lent date."
            )

        lent_updates[
            "expected_return_date"
        ] = (
            value.isoformat()
            if value
            else None
        )

    # --------------------------------------------------------
    # Validate notes
    # --------------------------------------------------------

    if "notes" in lent_updates:

        notes = lent_updates["notes"]

        if notes is not None:

            notes = notes.strip()

            if len(notes) > 500:
                raise ValueError(
                    "Notes cannot exceed 500 characters."
                )

        lent_updates["notes"] = (
            notes or None
            if notes is not None
            else None
        )

    # --------------------------------------------------------
    # Update receivable
    # --------------------------------------------------------

    if lent_updates:

        updated = (
            get_table("money_lent")
            .update(lent_updates)
            .eq("id", money_lent_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not updated.data:
            raise RuntimeError(
                "Money lent record could not be updated."
            )

    # --------------------------------------------------------
    # Synchronize linked transaction notes
    # --------------------------------------------------------

    if "notes" in updates:

        transaction_update = (
            get_table("transactions")
            .update(
                {
                    "notes": lent_updates.get(
                        "notes"
                    )
                }
            )
            .eq(
                "id",
                record["transaction_id"],
            )
            .eq(
                "user_id",
                user_id,
            )
            .execute()
        )

        if not transaction_update.data:
            raise RuntimeError(
                "Linked transaction could not be updated."
            )

    # --------------------------------------------------------
    # Return final record
    # --------------------------------------------------------

    final_response = (
        get_table("money_lent")
        .select("*")
        .eq("id", money_lent_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not final_response.data:
        raise RuntimeError(
            "Money lent record could not be retrieved."
        )

    return final_response.data[0]