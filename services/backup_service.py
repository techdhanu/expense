import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from database.queries import get_table


BACKUP_TABLES = [
    "app_users",
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
    "backup_history",
    "app_settings",
]

BACKUP_VERSION = "1.0"


def collect_backup_data() -> dict:
    """
    Collect application data from all backup-supported tables.
    """

    backup_data = {
        "backup_version": BACKUP_VERSION,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "tables": {},
    }

    for table_name in BACKUP_TABLES:
        response = (
            get_table(table_name)
            .select("*")
            .execute()
        )

        backup_data["tables"][table_name] = (
            response.data or []
        )

    return backup_data


def create_json_backup(
    output_directory: str = "backups",
) -> Path:
    """
    Create a JSON backup file locally.
    """

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
        for records in backup_data["tables"].values()
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
    Create one CSV file for each database table.
    """

    output_path = Path(output_directory)
    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    created_files = []

    for table_name in BACKUP_TABLES:

        response = (
            get_table(table_name)
            .select("*")
            .execute()
        )

        records = response.data or []

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

    record_backup_history(
        backup_type="csv",
        filename=f"csv_backup_{timestamp}",
        record_count=len(created_files),
    )

    return created_files


def record_backup_history(
    backup_type: str,
    filename: str,
    record_count: int,
) -> dict:
    """
    Record backup metadata in Supabase.
    """

    if backup_type not in {
        "json",
        "csv",
    }:
        raise ValueError(
            "Invalid backup type."
        )

    response = (
        get_table("backup_history")
        .insert(
            {
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
    Return previous backup records.
    """

    response = (
        get_table("backup_history")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []