from openpyxl import load_workbook

from parser.normalizer import normalize_value
from parser.structure import (
    detect_header_row,
    detect_actual_header_row,
    detect_active_columns,
    detect_parent_headers,
    detect_blocks,
    get_row_values,
    is_empty_row,
)


def parse_row(
    worksheet,
    row_number,
    columns,
    sheet_name,
):
    cells = {}

    for column_number in columns:

        cell = worksheet.cell(
            row=row_number,
            column=column_number
        )

        value = normalize_value(
            cell.value
        )

        if value is None:
            continue

        cells[cell.coordinate] = {
            "column": column_number,
            "value": value,
        }

    return {
        "sheet": sheet_name,
        "row": row_number,
        "cells": cells,
    }


def build_columns(
    worksheet,
    header_row,
    active_columns,
):
    """
    Build actual child columns.

    For normal sheets:
        header_row = actual header row.

    For grouped sheets:
        header_row = child header row.
    """

    columns = []

    for column_number in active_columns:

        cell = worksheet.cell(
            row=header_row,
            column=column_number
        )

        name = normalize_value(
            cell.value
        )

        columns.append({
            "index": column_number,
            "name": name,
            "coordinate": cell.coordinate,
        })

    return columns


def fill_merged_header_names(
    worksheet,
    columns,
    parent_headers,
):
    """
    Fill child headers represented by merged cells.

    Handles:
        Horizontal:
            A4:C4 = Item Details

        Vertical:
            H4:H5 = Status
    """

    for column in columns:

        if column["name"] is not None:
            continue

        column_number = column["index"]

        header_row = worksheet[
            column["coordinate"]
        ].row

        for merged_range in worksheet.merged_cells.ranges:

            if column_number not in range(
                merged_range.min_col,
                merged_range.max_col + 1
            ):
                continue

            if header_row not in range(
                merged_range.min_row,
                merged_range.max_row + 1
            ):
                continue

            value = worksheet.cell(
                row=merged_range.min_row,
                column=merged_range.min_col
            ).value

            if value is not None:
                column["name"] = str(value).strip()
                break

    return columns


def parse_sheet(worksheet):

    detected_header_row = detect_header_row(
        worksheet
    )

    actual_header_row = detect_actual_header_row(
        worksheet,
        detected_header_row
    )

    active_columns = detect_active_columns(
        worksheet,
        start_row=actual_header_row or 1,
    )

    parent_headers = detect_parent_headers(
        worksheet,
        detected_header_row,
        actual_header_row,
    )

    columns = []

    if actual_header_row:

        columns = build_columns(
            worksheet,
            actual_header_row,
            active_columns,
        )

        columns = fill_merged_header_names(
            worksheet,
            columns,
            parent_headers,
        )

    blocks = []

    if actual_header_row:

        detected_blocks = detect_blocks(
            worksheet,
            actual_header_row + 1,
        )

        for block_index, row_numbers in enumerate(
            detected_blocks,
            start=1
        ):

            rows = []

            for row_number in row_numbers:

                row = parse_row(
                    worksheet,
                    row_number,
                    active_columns,
                    worksheet.title,
                )

                if row["cells"]:
                    rows.append(row)

            if rows:

                blocks.append({
                    "block_id": block_index,
                    "rows": rows,
                })

    else:

        rows = []

        for row_number in range(
            1,
            worksheet.max_row + 1
        ):

            values = get_row_values(
                worksheet,
                row_number
            )

            if is_empty_row(values):
                continue

            row = parse_row(
                worksheet,
                row_number,
                active_columns,
                worksheet.title,
            )

            rows.append(row)

        if rows:

            blocks.append({
                "block_id": 1,
                "rows": rows,
            })

    return {
        "name": worksheet.title,

        "dimensions": {
            "rows": worksheet.max_row,
            "columns": worksheet.max_column,
        },

        # Keep the original detected row for
        # backwards compatibility.
        "header_row": detected_header_row,

        # New semantic header information.
        "actual_header_row": actual_header_row,

        "parent_headers": parent_headers,

        "columns": columns,

        "merged_ranges": [
            str(r)
            for r in worksheet.merged_cells.ranges
        ],

        "blocks": blocks,
    }


def parse_xlsx(file_path):

    workbook = load_workbook(
        file_path,
        data_only=True,
    )

    return {
        "file": file_path,

        "sheets": [
            parse_sheet(worksheet)
            for worksheet in workbook.worksheets
        ],
    }