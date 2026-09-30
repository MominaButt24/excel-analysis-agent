from typing import Any

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

    values = []

    for row in rows:

        for coordinate, cell in row["cells"].items():

            if coordinate.startswith(column):
                values.append(cell["value"])

    return values


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
    """Find minimum numeric value."""

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

    return min(numeric_values)


def maximum(rows, column):
    """Find maximum numeric value."""

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

    return max(numeric_values)


def search(rows, column, query):
    """
    Search for rows where a column contains text.
    """

    results = []

    query = str(query).lower()

    for row in rows:

        for coordinate, cell in row["cells"].items():

            if not coordinate.startswith(column):
                continue

            value = cell["value"]

            if value is None:
                continue

            if query in str(value).lower():
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

        for coordinate, cell in row["cells"].items():

            if not coordinate.startswith(column):
                continue

            cell_value = cell["value"]

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

            break

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

        for coordinate, cell in row["cells"].items():

            if coordinate.startswith(column):
                return cell["value"]

        return None

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