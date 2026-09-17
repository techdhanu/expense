import streamlit as st
from pathlib import Path
from datetime import datetime

from components.navigation import (
    setup_page,
    require_login,
    show_app_header,
)

from services.backup_service import (
    create_json_backup,
    create_csv_backups,
    restore_json_backup,
    get_backup_history,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

setup_page(
    "Backup & Restore",
    "💾",
    "wide",
)

require_login()

show_app_header(
    "Backup & Restore",
    "Protect your financial records with local backups.",
)


# =========================================================
# INFORMATION
# =========================================================

st.info(
    """
    **Backup your expense tracker regularly.**

    • JSON backup contains the complete application data.  
    • CSV backup creates a separate CSV file for each table.  
    • JSON backups can be restored through this page.  
    • CSV files are intended for viewing, analysis, and external storage.  
    • Restoring a backup uses the database restore function as one transaction.
    """
)


# =========================================================
# CREATE BACKUPS
# =========================================================

st.markdown("## 📦 Create Backup")

json_col, csv_col = st.columns(2)


# =========================================================
# JSON BACKUP
# =========================================================

with json_col:

    st.markdown("### 🗄️ Complete JSON Backup")

    st.caption(
        "Recommended for restoring your complete application data."
    )

    if st.button(
        "📥 Create JSON Backup",
        use_container_width=True,
        type="primary",
    ):

        try:

            with st.spinner(
                "Creating JSON backup..."
            ):

                json_path = create_json_backup()

            if json_path.exists():

                st.success(
                    "JSON backup created successfully."
                )

                with json_path.open(
                    "rb"
                ) as backup_file:

                    st.download_button(
                        "⬇️ Download JSON Backup",
                        data=backup_file.read(),
                        file_name=json_path.name,
                        mime="application/json",
                        use_container_width=True,
                    )

        except Exception as exc:

            st.error(
                "JSON backup could not be created."
            )

            st.caption(
                str(exc)
            )


# =========================================================
# CSV BACKUP
# =========================================================

with csv_col:

    st.markdown("### 📊 CSV Backup")

    st.caption(
        "Creates one CSV file for every supported database table."
    )

    if st.button(
        "📊 Create CSV Backups",
        use_container_width=True,
    ):

        try:

            with st.spinner(
                "Creating CSV backups..."
            ):

                csv_paths = create_csv_backups()

            if csv_paths:

                st.success(
                    f"{len(csv_paths)} CSV backup files created."
                )

                st.session_state[
                    "latest_csv_backups"
                ] = [
                    str(path)
                    for path in csv_paths
                    if path.exists()
                ]

        except Exception as exc:

            st.error(
                "CSV backups could not be created."
            )

            st.caption(
                str(exc)
            )


# =========================================================
# CSV DOWNLOADS
# =========================================================

latest_csv_backups = st.session_state.get(
    "latest_csv_backups",
    [],
)


if latest_csv_backups:

    st.divider()

    st.markdown(
        "### ⬇️ Download CSV Files"
    )

    st.caption(
        "Download the generated table backups individually."
    )

    for index in range(
        0,
        len(latest_csv_backups),
        3,
    ):

        row = latest_csv_backups[
            index:index + 3
        ]

        columns = st.columns(
            len(row)
        )

        for column, path_string in zip(
            columns,
            row,
        ):

            path = Path(
                path_string
            )

            with column:

                if path.exists():

                    with path.open(
                        "rb"
                    ) as csv_file:

                        st.download_button(
                            label=f"⬇️ {path.stem.split('_')[0]}",
                            data=csv_file.read(),
                            file_name=path.name,
                            mime="text/csv",
                            use_container_width=True,
                            key=f"download_csv_{path.name}",
                        )


# =========================================================
# RESTORE
# =========================================================

st.divider()

st.markdown("## ♻️ Restore Backup")

st.warning(
    """
    **Restore replaces/updates records using the database restore process.**

    Make sure you select the correct backup file before restoring.
    The restore operation is designed to execute atomically: if the
    database restore fails, PostgreSQL rolls back the transaction.
    """
)


uploaded_file = st.file_uploader(
    "Upload JSON Backup",
    type=["json"],
    help="Only JSON backups created by this application can be restored.",
)


if uploaded_file is not None:

    st.success(
        f"Selected: **{uploaded_file.name}**"
    )

    file_size_kb = (
        uploaded_file.size / 1024
        if uploaded_file.size
        else 0
    )

    st.caption(
        f"File size: {file_size_kb:.2f} KB"
    )


    # -----------------------------------------------------
    # SAVE UPLOADED FILE TEMPORARILY
    # -----------------------------------------------------

    if st.button(
        "🔍 Validate & Restore Backup",
        use_container_width=True,
        type="primary",
    ):

        import tempfile

        temp_path = None

        try:

            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=".json",
                delete=False,
            ) as temp_file:

                temp_file.write(
                    uploaded_file.getvalue()
                )

                temp_path = Path(
                    temp_file.name
                )


            with st.spinner(
                "Restoring backup..."
            ):

                result = restore_json_backup(
                    temp_path
                )


            st.success(
                "Backup restored successfully."
            )


            # -------------------------------------------------
            # RESTORE RESULT
            # -------------------------------------------------

            if isinstance(result, dict):

                restored_count = result.get(
                    "record_count"
                )

                if restored_count is not None:

                    st.metric(
                        "Records Restored",
                        restored_count,
                    )


                message = result.get(
                    "message"
                )

                if message:

                    st.info(
                        str(message)
                    )


                # Display additional safe result fields.
                display_items = {
                    key: value
                    for key, value in result.items()
                    if key not in {
                        "message",
                        "record_count",
                    }
                }


                if display_items:

                    with st.expander(
                        "Restore Details"
                    ):

                        for key, value in display_items.items():

                            st.write(
                                f"**{key.replace('_', ' ').title()}:** "
                                f"{value}"
                            )


        except FileNotFoundError as exc:

            st.error(
                str(exc)
            )

        except ValueError as exc:

            st.error(
                f"Backup validation failed: {exc}"
            )

        except RuntimeError as exc:

            st.error(
                f"Backup restore failed: {exc}"
            )

        except Exception as exc:

            st.error(
                "An unexpected error occurred during restore."
            )

            st.caption(
                str(exc)
            )

        finally:

            if temp_path and temp_path.exists():

                try:

                    temp_path.unlink()

                except OSError:

                    pass


# =========================================================
# BACKUP HISTORY
# =========================================================

st.divider()

st.markdown("## 🕘 Backup History")


try:

    backup_history = get_backup_history()

except Exception as exc:

    st.error(
        "Backup history could not be loaded."
    )

    st.caption(
        str(exc)
    )

    backup_history = []


if not backup_history:

    st.info(
        "No backup history is available yet."
    )

else:

    history_rows = []

    for record in backup_history:

        created_at = record.get(
            "created_at"
        )

        if created_at:

            try:

                formatted_date = (
                    datetime.fromisoformat(
                        str(created_at).replace(
                            "Z",
                            "+00:00",
                        )
                    ).strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                )

            except ValueError:

                formatted_date = str(
                    created_at
                )

        else:

            formatted_date = "Unknown"


        backup_type = record.get(
            "backup_type",
            "",
        )

        history_rows.append(
            {
                "Date": formatted_date,
                "Type": backup_type.upper(),
                "Filename": record.get(
                    "backup_filename",
                    "",
                ),
                "Version": record.get(
                    "backup_version",
                    "",
                ),
                "Records": record.get(
                    "record_count",
                    0,
                ),
            }
        )


    st.dataframe(
        history_rows,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# SECURITY NOTE
# =========================================================

st.divider()

st.markdown(
    "### 🔐 Backup Security"
)

st.warning(
    """
    **Keep downloaded backups private.**

    Backup files contain application data and may contain sensitive
    financial information. Store them somewhere secure and do not
    upload them to public repositories or share them publicly.

    The current backup service also includes the `app_users` table,
    so backup files may contain password hashes. Never publish these
    backup files or commit them to GitHub.
    """
)


# =========================================================
# BEST PRACTICE
# =========================================================

st.markdown(
    "### ✅ Recommended Backup Practice"
)

st.markdown(
    """
    **For normal use:**

    1. Create a JSON backup.
    2. Download it to a secure location.
    3. Optionally create CSV backups for analysis.
    4. Keep at least one backup outside the project folder.
    5. Do not commit backup files to Git.
    6. Periodically test restoring a backup.
    """
)

st.caption(
    "💾 Your backup is only useful if you can safely restore it."
)