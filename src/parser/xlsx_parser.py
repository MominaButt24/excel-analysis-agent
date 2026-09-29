from datetime import datetime, date
import re

from openpyxl import load_workbook


def normalize_text(value):
    """
    Normalize text without changing its meaning.
    """

    if value is None:
        return None

    if isinstance(value, str):
        value = " ".join(value.split())
        return value if value else None

    return value


def normalize_date(value):
    """
    Normalize actual Excel dates and common date strings.

    If a value cannot safely be interpreted as a date,
    keep the original value.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if not isinstance(value, str):
        return value

    value = value.strip()

    # Keep non-date text untouched.
    if not re.search(r"\d", value):
        return value

    # Normalize repeated separators.
    normalized = re.sub(r"[-\s]+", "-", value)

    parts = normalized.split("-")

    # Examples:
    # 12-08-2026
    # 12-8-26
    # 21--7-26
    if len(parts) == 3:

        try:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])

            if year < 100:
                year += 2000

            return date(
                year,
                month,
                day
            ).isoformat()

        except ValueError:
            pass

    # Example:
    # 30-726 -> 30-7-26
    match = re.fullmatch(
        r"(\d{1,2})-(\d)(\d{2})",
        normalized
    )

    if match:

        try:
            day = int(match.group(1))
            month = int(match.group(2))
            year = 2000 + int(match.group(3))

            return date(
                year,
                month,
                day
            ).isoformat()

        except ValueError:
            pass

    return value


def normalize_value(value):
    """
    Normalize a cell value while preserving its meaning.
    """

    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return normalize_date(value)

    if isinstance(value, str):

        text = normalize_text(value)

        if text is None:
            return None

        # Try date normalization.
        normalized_date = normalize_date(text)

        return normalized_date

    return value


def is_empty_row(values):
    """
    Check whether a complete worksheet row is empty.
    """

    return all(
        value is None
        for value in values
    )


def detect_header_row(worksheet):
    """
    Detect a likely table header row.

    This is structural detection only.

    We don't assume:
    - row 1 is the header
    - specific column names
    - a specific spreadsheet type

    A row is considered a possible header when it contains
    multiple non-empty text values.
    """

    for row_number in range(
        1,
        worksheet.max_row + 1
    ):

        values = [
            worksheet.cell(
                row=row_number,
                column=column_number
            ).value
            for column_number in range(
                1,
                worksheet.max_column + 1
            )
        ]

        non_empty = [
            value
            for value in values
            if value is not None
        ]

        if len(non_empty) < 2:
            continue

        text_values = [
            value
            for value in non_empty
            if isinstance(value, str)
        ]

        # A header usually contains multiple text labels.
        if len(text_values) >= 2:
            return row_number

    return None


def extract_columns(worksheet, header_row):
    """
    Extract only columns that contain actual information
    somewhere in the worksheet.

    Excel's max_column can be larger than the real table
    because of formatting.
    """

    active_columns = []

    for column_number in range(
        1,
        worksheet.max_column + 1
    ):

        has_value = False

        for row_number in range(
            header_row,
            worksheet.max_row + 1
        ):

            value = worksheet.cell(
                row=row_number,
                column=column_number
            ).value

            if value is not None:
                has_value = True
                break

        if not has_value:
            continue

        header_value = worksheet.cell(
            row=header_row,
            column=column_number
        ).value

        active_columns.append({
            "index": column_number,
            "name": normalize_value(header_value),
        })

    return active_columns


def extract_row(worksheet, row_number, columns):
    """
    Extract a row using the detected column structure.
    """

    values = {}

    for column in columns:

        column_name = column["name"]

        value = worksheet.cell(
            row=row_number,
            column=column["index"]
        ).value

        value = normalize_value(value)

        # Preserve duplicate/empty headers safely.
        if column_name is None:
            key = f"column_{column['index']}"

        else:
            key = str(column_name)

        if key in values:
            key = f"{key}_{column['index']}"

        values[key] = value

    return values


def parse_merged_ranges(worksheet):
    """
    Preserve merged-cell information.
    """

    return [
        str(range_)
        for range_ in worksheet.merged_cells.ranges
    ]


def parse_xlsx(file_path: str):

    workbook = load_workbook(
        file_path,
        data_only=True
    )

    workbook_data = {
        "file": file_path,
        "sheets": []
    }

    for worksheet in workbook.worksheets:

        header_row = detect_header_row(worksheet)

        sheet_data = {
            "name": worksheet.title,
            "dimensions": {
                "max_row": worksheet.max_row,
                "max_column": worksheet.max_column,
            },
            "merged_ranges": parse_merged_ranges(
                worksheet
            ),
            "header_row": header_row,
            "columns": [],
            "rows": [],
        }

        # No header detected.
        #
        # Still preserve the sheet's raw structure.
        if header_row is None:

            for row_number in range(
                1,
                worksheet.max_row + 1
            ):

                raw_values = [
                    normalize_value(
                        worksheet.cell(
                            row=row_number,
                            column=column_number
                        ).value
                    )
                    for column_number in range(
                        1,
                        worksheet.max_column + 1
                    )
                ]

                if is_empty_row(raw_values):
                    continue

                sheet_data["rows"].append({
                    "row_number": row_number,
                    "values": raw_values,
                })

            workbook_data["sheets"].append(
                sheet_data
            )

            continue

        # Header found.
        sheet_data["columns"] = extract_columns(
            worksheet,
            header_row
        )

        # Extract rows after header.
        for row_number in range(
            header_row + 1,
            worksheet.max_row + 1
        ):

            raw_values = [
                worksheet.cell(
                    row=row_number,
                    column=column_number
                ).value
                for column_number in range(
                    1,
                    worksheet.max_column + 1
                )
            ]

            if is_empty_row(raw_values):
                continue

            row_values = extract_row(
                worksheet,
                row_number,
                sheet_data["columns"]
            )

            sheet_data["rows"].append({
                "row_number": row_number,
                "values": row_values,
            })

        workbook_data["sheets"].append(
            sheet_data
        )

    return workbook_data