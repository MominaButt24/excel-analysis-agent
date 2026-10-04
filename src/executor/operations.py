from typing import Any
from datetime import date
from openpyxl.utils.cell import column_index_from_string
from parser.normalizer import normalize_value


def get_row_value(row, column):
    values = row.get("values")

    if values is not None:
        return values.get(column)

    column_index = column_index_from_string(column)

    for cell in row["cells"].values():
        if cell["column"] == column_index:
            return cell["value"]

    return None

def get_rows(parsed_workbook):
    """
    Convert parsed workbook blocks into a flat list of rows.

    Each row keeps:
    - sheet
    - original Excel row number
    - cell coordinates
    - values
    """

    rows = []

    for sheet in parsed_workbook["sheets"]:

        for block in sheet["blocks"]:

            for row in block["rows"]:

                rows.append(row)

    return rows


def row_to_dict(row):
    """
    Convert parser row format into a simple dictionary.

    Example:

    {
        "A6": {"column": 1, "value": "EL-1001"},
        "B6": {"column": 2, "value": "Wireless Mouse"}
    }

    becomes:

    {
        "A6": "EL-1001",
        "B6": "Wireless Mouse"
    }
    """

    return {
        coordinate: cell["value"]
        for coordinate, cell in row["cells"].items()
    }


def get_column_values(rows, column):
    """
    Get values from a specific Excel column.

    Example:
        get_column_values(rows, "D")
    """

    return [
        value
        for row in rows
        if (value := get_row_value(row, column)) is not None
    ]


def count(rows):
    """Count rows."""

    return len(rows)


def unique(rows, column):
    """Return unique values from a column."""

    values = get_column_values(
        rows,
        column
    )

    return list(dict.fromkeys(values))


def sum_column(rows, column):
    """Calculate sum of numeric values."""

    values = get_column_values(
        rows,
        column
    )

    numeric_values = [
        value
        for value in values
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
    ]

    return sum(numeric_values)


def average(rows, column):
    """Calculate average of numeric values."""

    values = get_column_values(
        rows,
        column
    )

    numeric_values = [
        value
        for value in values
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
    ]

    if not numeric_values:
        return None

    return sum(numeric_values) / len(numeric_values)


def minimum(rows, column):
    """Find the minimum numeric value or earliest ISO date."""

    values = get_column_values(
        rows,
        column
    )

    numeric_values = [
        value
        for value in values
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
    ]

    if numeric_values:
        return min(numeric_values)

    date_values = _iso_date_values(values)
    return min(date_values) if date_values else None


def maximum(rows, column):
    """Find the maximum numeric value or latest ISO date."""

    values = get_column_values(
        rows,
        column
    )

    numeric_values = [
        value
        for value in values
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
    ]

    if numeric_values:
        return max(numeric_values)

    date_values = _iso_date_values(values)
    return max(date_values) if date_values else None


def _iso_date_values(values):
    if not values or not all(isinstance(value, str) for value in values):
        return []

    for value in values:
        try:
            date.fromisoformat(value)
        except ValueError:
            return []

    return values


def search(rows, column, query):
    """
    Search for rows where a column contains text.
    """

    results = []

    query = str(normalize_value(str(query))).lower()

    for row in rows:
        value = get_row_value(row, column)

        if value is not None and query in str(value).lower():
            results.append(row)

    return results


def filter_rows(
    rows,
    column,
    operator,
    value,
):
    """
    Filter rows using a comparison.

    Supported operators:
        ==
        !=
        >
        <
        >=
        <=
    """

    results = []

    for row in rows:
        cell_value = get_row_value(row, column)

        try:
            if operator == "==":
                matched = cell_value == value
            elif operator == "!=":
                matched = cell_value != value
            elif operator == ">":
                matched = cell_value > value
            elif operator == "<":
                matched = cell_value < value
            elif operator == ">=":
                matched = cell_value >= value
            elif operator == "<=":
                matched = cell_value <= value
            else:
                raise ValueError(
                    f"Unsupported operator: {operator}"
                )
        except TypeError:
            matched = False

        if matched:
            results.append(row)

    return results

def filter_rows_multiple(rows, conditions):
    """
    Apply multiple filter conditions using AND logic.

    Supports:
        column -> fixed value

    and:
        column -> another column

    Also supports grouped/implicitly repeated values
    through forward-fill semantics.
    """

    results = []

    for row in rows:
        matched = True

        for condition in conditions:
            left_value = get_row_value(
                row,
                condition["column"],
            )

            if "value_from_column" in condition:
                right_value = get_row_value(
                    row,
                    condition["value_from_column"],
                )

            else:
                right_value = normalize_value(
                    condition.get("value")
                )

            operator = condition["operator"]

            try:

                if operator == "==":

                    if isinstance(left_value, str) and isinstance(
                        right_value, str
                    ):
                        condition_match = (
                            left_value.strip().lower()
                            == right_value.strip().lower()
                        )
                    else:
                        condition_match = (
                            left_value == right_value
                        )

                elif operator == "!=":

                    if isinstance(left_value, str) and isinstance(
                        right_value, str
                    ):
                        condition_match = (
                            left_value.strip().lower()
                            != right_value.strip().lower()
                        )
                    else:
                        condition_match = (
                            left_value != right_value
                        )

                elif operator == ">":
                    condition_match = (
                        left_value > right_value
                    )

                elif operator == "<":
                    condition_match = (
                        left_value < right_value
                    )

                elif operator == ">=":
                    condition_match = (
                        left_value >= right_value
                    )

                elif operator == "<=":
                    condition_match = (
                        left_value <= right_value
                    )

                else:
                    raise ValueError(
                        f"Unsupported operator: {operator}"
                    )

            except TypeError:
                condition_match = False

            if not condition_match:
                matched = False
                break

        if matched:
            results.append(row)

    return results

def sort_rows(
    rows,
    column,
    descending=False,
):
    """
    Sort rows by a column.

    Rows with missing values are placed last.
    Mixed data types are handled safely.
    """

    def get_value(row):
        return get_row_value(row, column)

    def sort_key(row):

        value = get_value(row)

        if value is None:
            return (2, "")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return (0, value)

        return (1, str(value).lower())

    return sorted(
        rows,
        key=sort_key,
        reverse=descending,
    )

def forward_fill_column(rows, column):
    """
    Return row-level values for a column, carrying the
    last non-empty value forward.

    The original parsed rows are not modified.
    """

    filled_values = {}

    current_value = None

    for row in rows:
        row_number = row["row"]

        value = None

        for coordinate, cell in row["cells"].items():
            if coordinate.startswith(column):
                value = cell["value"]
                break

        if value is not None:
            current_value = value

        filled_values[row_number] = current_value

    return filled_values