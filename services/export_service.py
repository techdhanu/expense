from io import BytesIO
from decimal import Decimal

import pandas as pd


# ---------------------------------------------------------
# TRANSACTION TYPE LABELS
# ---------------------------------------------------------
TRANSACTION_TYPE_LABELS = {
    "income": "Income",
    "expense": "Expense",
    "internal_transfer": "Transfer",
    "friend_money_received": "Friend Money Received",
    "friend_money_returned": "Friend Money Returned",
    "balance_adjustment": "Balance Adjustment",
    "savings_goal_contribution": "Savings Contribution",
}


# ---------------------------------------------------------
# DECIMAL HELPER
# ---------------------------------------------------------
def _to_decimal(value) -> Decimal:
    """
    Convert a monetary value safely to Decimal.

    Never performs financial calculations using float.
    """
    return Decimal(str(value if value is not None else "0"))


# ---------------------------------------------------------
# BUILD EXPORT DATAFRAME
# ---------------------------------------------------------
def build_transaction_dataframe(
    transactions: list[dict],
    account_map: dict[str, str],
    category_map: dict[str, str],
    person_map: dict[str, str],
) -> pd.DataFrame:
    """
    Convert transaction records into a clean export DataFrame.

    The function does not modify the original transaction data.
    """

    rows = []

    for transaction in transactions:

        transaction_type = transaction.get(
            "transaction_type"
        )

        source_account_id = transaction.get(
            "source_account_id"
        )

        destination_account_id = transaction.get(
            "destination_account_id"
        )

        category_id = transaction.get(
            "category_id"
        )

        person_id = transaction.get(
            "person_id"
        )

        # ---------------------------------------------
        # ACCOUNT
        # ---------------------------------------------
        if transaction_type == "internal_transfer":

            source_name = account_map.get(
                source_account_id,
                "Unknown Account",
            )

            destination_name = account_map.get(
                destination_account_id,
                "Unknown Account",
            )

            account_display = (
                f"{source_name} → {destination_name}"
            )

        else:

            account_display = account_map.get(
                source_account_id,
                "Unknown Account",
            )

        # ---------------------------------------------
        # CATEGORY
        # ---------------------------------------------
        category_display = category_map.get(
            category_id,
            "—",
        )

        # ---------------------------------------------
        # PERSON
        # ---------------------------------------------
        person_display = person_map.get(
            person_id,
            "—",
        )

        # ---------------------------------------------
        # AMOUNT
        # ---------------------------------------------
        amount = _to_decimal(
            transaction.get("amount", "0")
        )

        # ---------------------------------------------
        # DATE
        # ---------------------------------------------
        transaction_date = transaction.get(
            "transaction_date"
        )

        # ---------------------------------------------
        # ROW
        # ---------------------------------------------
        rows.append(
            {
                "Date": transaction_date,
                "Type": TRANSACTION_TYPE_LABELS.get(
                    transaction_type,
                    transaction_type or "Unknown",
                ),
                "Account": account_display,
                "Category": category_display,
                "Person": person_display,
                "Amount": amount,
                "Description": (
                    transaction.get("description")
                    or "—"
                ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "Date",
            "Type",
            "Account",
            "Category",
            "Person",
            "Amount",
            "Description",
        ],
    )


# ---------------------------------------------------------
# CSV EXPORT
# ---------------------------------------------------------
def export_transactions_csv(
    dataframe: pd.DataFrame,
) -> bytes:
    """
    Export transactions to CSV bytes.
    """

    export_df = dataframe.copy()

    if "Amount" in export_df.columns:
        export_df["Amount"] = export_df[
            "Amount"
        ].apply(
            lambda value: f"{_to_decimal(value):.2f}"
        )

    return export_df.to_csv(
        index=False
    ).encode("utf-8-sig")


# ---------------------------------------------------------
# EXCEL EXPORT
# ---------------------------------------------------------
def export_transactions_excel(
    dataframe: pd.DataFrame,
) -> bytes:
    """
    Export transactions to an Excel workbook.

    The workbook is created in memory and returned as bytes.
    """

    output = BytesIO()

    export_df = dataframe.copy()

    if "Amount" in export_df.columns:
        export_df["Amount"] = export_df[
            "Amount"
        ].apply(
            lambda value: float(
                _to_decimal(value)
            )
        )

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        export_df.to_excel(
            writer,
            index=False,
            sheet_name="Transactions",
        )

        worksheet = writer.book["Transactions"]

        # Freeze header row
        worksheet.freeze_panes = "A2"

        # Auto-size columns
        for column_cells in worksheet.columns:

            max_length = 0

            column_letter = (
                column_cells[0].column_letter
            )

            for cell in column_cells:

                if cell.value is not None:
                    max_length = max(
                        max_length,
                        len(str(cell.value)),
                    )

            worksheet.column_dimensions[
                column_letter
            ].width = min(
                max_length + 2,
                50,
            )

        # INR-style number format
        amount_column = None

        for cell in worksheet[1]:

            if cell.value == "Amount":
                amount_column = cell.column_letter
                break

        if amount_column:

            for row in range(
                2,
                worksheet.max_row + 1,
            ):
                worksheet[
                    f"{amount_column}{row}"
                ].number_format = '#,##0.00'

    return output.getvalue()


# ---------------------------------------------------------
# PDF EXPORT
# ---------------------------------------------------------
def export_transactions_pdf(
    dataframe: pd.DataFrame,
    title: str = "Transaction History",
) -> bytes:
    """
    Export transactions to a PDF document.

    The PDF is generated completely in memory.
    """

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()

    story = []

    # ---------------------------------------------
    # TITLE
    # ---------------------------------------------
    story.append(
        Paragraph(
            title,
            styles["Title"],
        )
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    # ---------------------------------------------
    # EMPTY DATASET
    # ---------------------------------------------
    if dataframe.empty:

        story.append(
            Paragraph(
                "No transactions found.",
                styles["Normal"],
            )
        )

        document.build(story)

        return output.getvalue()

    # ---------------------------------------------
    # PREPARE TABLE DATA
    # ---------------------------------------------
    export_df = dataframe.copy()

    if "Amount" in export_df.columns:
        export_df["Amount"] = export_df[
            "Amount"
        ].apply(
            lambda value: (
                f"₹{_to_decimal(value):,.2f}"
            )
        )

    table_data = [
        list(export_df.columns)
    ]

    for row in export_df.itertuples(
        index=False,
        name=None,
    ):
        table_data.append(
            [
                str(value)
                for value in row
            ]
        )

    # ---------------------------------------------
    # TABLE
    # ---------------------------------------------
    table = Table(
        table_data,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    story.append(table)

    # ---------------------------------------------
    # BUILD PDF
    # ---------------------------------------------
    document.build(story)

    return output.getvalue()