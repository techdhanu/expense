from pathlib import Path
import json

import pytest

from database.queries import get_table
from services.backup_service import (
    BACKUP_VERSION,
    collect_backup_data,
    create_json_backup,
    create_csv_backups,
    restore_json_backup,
)


def test_collect_backup_data():
    backup_data = collect_backup_data()

    assert isinstance(backup_data, dict)
    assert backup_data["backup_version"] == BACKUP_VERSION
    assert backup_data["backup_version"] == "1.1"
    assert "created_at" in backup_data
    assert "tables" in backup_data
    assert "user_id" in backup_data

    expected_tables = {
        "accounts",
        "categories",
        "transactions",
        "transfers",
        "people",
        "friends_money",
        "budgets",
        "savings_goals",
        "savings_contributions",
        "recurring_transactions",
        "backup_history",
        "app_settings",
        "money_lent",
    }

    actual_tables = set(backup_data["tables"].keys())

    assert expected_tables.issubset(actual_tables)

    # Password hashes / authentication records must never be included.
    assert "app_users" not in actual_tables


def test_create_json_backup(tmp_path):
    backup_file = create_json_backup(str(tmp_path))

    assert isinstance(backup_file, Path)
    assert backup_file.exists()
    assert backup_file.suffix == ".json"

    with backup_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert isinstance(data, dict)
    assert data["backup_version"] == "1.1"
    assert "user_id" in data
    assert "tables" in data
    assert isinstance(data["tables"], dict)

    # Authentication data must never be exported.
    assert "app_users" not in data["tables"]


def test_create_csv_backups(tmp_path):
    csv_files = create_csv_backups(str(tmp_path))

    assert isinstance(csv_files, list)
    assert len(csv_files) > 0

    for csv_file in csv_files:
        assert isinstance(csv_file, Path)
        assert csv_file.exists()
        assert csv_file.suffix == ".csv"


def test_restore_json_backup_success(tmp_path):
    backup_data = collect_backup_data()

    backup_file = tmp_path / "valid_backup.json"
    backup_file.write_text(
        json.dumps(backup_data),
        encoding="utf-8",
    )

    result = restore_json_backup(backup_file)

    expected_total = sum(
        len(records)
        for records in backup_data["tables"].values()
    )


    assert result["backup_version"] == "1.1"
    assert result["total_records"] == expected_total


def test_restore_invalid_json_rejected(tmp_path):
    backup_file = tmp_path / "invalid.json"

    backup_file.write_text(
        "{ this is not valid json",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        restore_json_backup(backup_file)


def test_restore_wrong_version_rejected(tmp_path):
    backup_data = collect_backup_data()
    backup_data["backup_version"] = "999.0"

    backup_file = tmp_path / "wrong_version.json"

    backup_file.write_text(
        json.dumps(backup_data),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported backup version"):
        restore_json_backup(backup_file)


def test_restore_missing_table_rejected(tmp_path):
    backup_data = collect_backup_data()

    del backup_data["tables"]["accounts"]

    backup_file = tmp_path / "missing_table.json"

    backup_file.write_text(
        json.dumps(backup_data),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Backup is missing tables"):
        restore_json_backup(backup_file)


def test_restore_is_atomic_on_database_failure(tmp_path):
    backup_data = collect_backup_data()

    accounts = backup_data["tables"]["accounts"]
    categories = backup_data["tables"]["categories"]

    if not accounts or not categories:
        pytest.skip(
            "Accounts and categories are required for atomicity test."
        )

    account_id = accounts[0]["id"]

    original_response = (
        get_table("accounts")
        .select("opening_balance")
        .eq("id", account_id)
        .limit(1)
        .execute()
    )

    assert original_response.data

    original_balance = original_response.data[0]["opening_balance"]

    # First make a valid change to an earlier table.
    accounts[0]["opening_balance"] = "999999.99"

    # Then deliberately make a later table invalid.
    categories[0]["category_type"] = "INVALID_CATEGORY_TYPE"

    backup_file = tmp_path / "atomic_failure.json"

    backup_file.write_text(
        json.dumps(backup_data),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="Atomic backup restore failed",
    ):
        restore_json_backup(backup_file)

    # The earlier account change must have been rolled back.
    final_response = (
        get_table("accounts")
        .select("opening_balance")
        .eq("id", account_id)
        .limit(1)
        .execute()
    )

    assert final_response.data
    assert final_response.data[0]["opening_balance"] == original_balance