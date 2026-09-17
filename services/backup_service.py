import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from database.client import get_supabase_client
from database.queries import get_table
from services.authentication_service import get_current_user_id


# Financial/application data only.
# app_users is intentionally excluded because it contains authentication data.
BACKUP_TABLES = [
    "accounts",
    "categories",
    "people",
    "transactions",
    "transfers",
    "friends_money",
    "budgets",
    "savings_goals",
    "savings_contributions",
    "recurring_transactions",
    "money_lent",
    "backup_history",
    "app_settings",
]

BACKUP_VERSION = "1.1"


def _get_user_id() -> str:
    """Return the authenticated user's ID."""

    return get_current_user_id()


def _get_user_table_data(
    table_name: str,
    user_id: str,
) -> list[dict]:
    """Return only records belonging to the current user."""

    response = (
        get_table(table_name)
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    return response.data or []


def collect_backup_data() -> dict:
    """
    Collect only the current user's application data.

    Authentication records are intentionally excluded.
    """

    user_id = _get_user_id()

    backup_data = {
        "backup_version": BACKUP_VERSION,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "user_id": user_id,
        "tables": {},
    }

    for table_name in BACKUP_TABLES:
        backup_data["tables"][table_name] = (
            _get_user_table_data(
                table_name,
                user_id,
            )
        )

    return backup_data


def create_json_backup(
    output_directory: str = "backups",
) -> Path:
    """
    Create a JSON backup containing only the current user's data.
    """

    _get_user_id()

    output_path = Path(output_directory)

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_data = collect_backup_data()

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"expense_tracker_backup_{timestamp}.json"
    )

    file_path = output_path / filename

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            backup_data,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    record_count = sum(
        len(records)
        for table_name, records
        in backup_data["tables"].items()
        if table_name != "backup_history"
    )

    record_backup_history(
        backup_type="json",
        filename=filename,
        record_count=record_count,
    )

    return file_path


def create_csv_backups(
    output_directory: str = "backups",
) -> list[Path]:
    """
    Create one CSV file per supported table.

    Every CSV contains only the current user's records.
    """

    user_id = _get_user_id()

    output_path = Path(output_directory)

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    created_files = []
    total_record_count = 0

    for table_name in BACKUP_TABLES:

        records = _get_user_table_data(
            table_name,
            user_id,
        )

        dataframe = pd.DataFrame(records)

        filename = (
            f"{table_name}_{timestamp}.csv"
        )

        file_path = output_path / filename

        dataframe.to_csv(
            file_path,
            index=False,
        )

        created_files.append(file_path)

        # Count database records, not generated files.
        if table_name != "backup_history":
            total_record_count += len(records)

    record_backup_history(
        backup_type="csv",
        filename=f"csv_backup_{timestamp}",
        record_count=total_record_count,
    )

    return created_files


def record_backup_history(
    backup_type: str,
    filename: str,
    record_count: int,
) -> dict:
    """
    Record backup metadata for the current user.
    """

    user_id = _get_user_id()

    if backup_type not in {
        "json",
        "csv",
    }:
        raise ValueError(
            "Invalid backup type."
        )

    if record_count < 0:
        raise ValueError(
            "Record count cannot be negative."
        )

    response = (
        get_table("backup_history")
        .insert(
            {
                "user_id": user_id,
                "backup_type": backup_type,
                "backup_filename": filename,
                "backup_version": BACKUP_VERSION,
                "record_count": record_count,
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Backup history could not be recorded."
        )

    return response.data[0]


def get_backup_history() -> list[dict]:
    """
    Return backup history for the current user only.
    """

    user_id = _get_user_id()

    response = (
        get_table("backup_history")
        .select("*")
        .eq("user_id", user_id)
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def _validate_backup_tables(
    tables: dict,
) -> None:
    """Validate that the backup contains the supported tables."""

    if not isinstance(tables, dict):
        raise ValueError(
            "Backup does not contain valid table data."
        )

    missing_tables = [
        table
        for table in BACKUP_TABLES
        if table not in tables
    ]

    if missing_tables:
        raise ValueError(
            "Backup is missing tables: "
            + ", ".join(missing_tables)
        )

    for table_name in BACKUP_TABLES:
        if not isinstance(
            tables[table_name],
            list,
        ):
            raise ValueError(
                f"Invalid data format for table: {table_name}"
            )


def _validate_backup_user(
    backup_data: dict,
) -> str:
    """
    Ensure the backup belongs to the currently
    authenticated user.
    """

    current_user_id = _get_user_id()

    backup_user_id = backup_data.get(
        "user_id"
    )

    if not backup_user_id:
        raise ValueError(
            "Backup does not contain a user ID."
        )

    if str(backup_user_id) != str(
        current_user_id
    ):
        raise ValueError(
            "This backup belongs to a different user."
        )

    return current_user_id


def restore_json_backup(
    backup_file: str | Path,
) -> dict:
    """
    Restore a JSON backup for the currently
    authenticated user.

    The database RPC performs the actual atomic restore.
    """

    current_user_id = _get_user_id()

    backup_path = Path(backup_file)

    if not backup_path.exists():
        raise FileNotFoundError(
            f"Backup file not found: {backup_path}"
        )

    if backup_path.suffix.lower() != ".json":
        raise ValueError(
            "Only JSON backup files can be restored."
        )

    try:
        with backup_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            backup_data = json.load(file)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "The backup file contains invalid JSON."
        ) from exc

    if not isinstance(
        backup_data,
        dict,
    ):
        raise ValueError(
            "Invalid backup format."
        )

    if backup_data.get(
        "backup_version"
    ) != BACKUP_VERSION:
        raise ValueError(
            "Unsupported backup version."
        )

    _validate_backup_user(
        backup_data
    )

    tables = backup_data.get(
        "tables"
    )

    _validate_backup_tables(
        tables
    )

    # Explicitly force the authenticated user's ID.
    # This prevents a crafted backup from attempting
    # to restore records under another user.
    backup_data["user_id"] = current_user_id

    # Also validate that every backed-up record has
    # the same user_id.
    for table_name in BACKUP_TABLES:
        for record in tables[table_name]:

            if not isinstance(
                record,
                dict,
            ):
                raise ValueError(
                    f"Invalid record in table: {table_name}"
                )

            record_user_id = record.get(
                "user_id"
            )

            if record_user_id is None:
                raise ValueError(
                    f"Record in {table_name} "
                    "does not contain user_id."
                )

            if str(record_user_id) != str(
                current_user_id
            ):
                raise ValueError(
                    f"Backup contains data belonging "
                    f"to another user in table: {table_name}"
                )

    try:
        response = (
            get_supabase_client()
            .rpc(
                "restore_expense_tracker_backup",
                {
                    "backup_data": backup_data,
                },
            )
            .execute()
        )

    except Exception as exc:
        raise RuntimeError(
            f"Atomic backup restore failed: {exc}"
        ) from exc

    if not response.data:
        raise RuntimeError(
            "Backup restore returned no result."
        )

    result = response.data

    if isinstance(
        result,
        list,
    ):
        result = (
            result[0]
            if result
            else {}
        )

    if not isinstance(
        result,
        dict,
    ):
        raise RuntimeError(
            "Backup restore returned an invalid result."
        )

    return result