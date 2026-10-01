from executor.operations import (
    count,
    sum_column,
    average,
    minimum,
    maximum,
    search,
    filter_rows_multiple,
    sort_rows,
)
from executor.resolver import resolve_column


def get_sheet(parsed_workbook, sheet_name):
    for sheet in parsed_workbook["sheets"]:
        if sheet["name"].strip().lower() == sheet_name.strip().lower():
            return sheet

    raise ValueError(
        f"Sheet '{sheet_name}' not found."
    )


def get_sheet_rows(sheet):
    rows = []

    for block in sheet["blocks"]:
        rows.extend(block["rows"])

    return rows


def execute_plan(parsed_workbook, plan):
    """
    Validate and execute an ExecutionPlan
    against the parsed workbook.
    """

    sheet = get_sheet(
        parsed_workbook,
        plan.sheet,
    )

    rows = get_sheet_rows(sheet)

    if plan.filters:
        resolved_filters = []

        for condition in plan.filters:

            resolved_condition = {
                **condition
            }

            column_info = resolve_column(
                parsed_workbook,
                plan.sheet,
                condition["column"],
            )

            resolved_condition["column"] = (
                column_info["column"]
            )

            if "value_from_column" in condition:

                comparison_info = resolve_column(
                    parsed_workbook,
                    plan.sheet,
                    condition["value_from_column"],
                )

                resolved_condition[
                    "value_from_column"
                ] = comparison_info["column"]

            resolved_filters.append(
                resolved_condition
            )

        rows = filter_rows_multiple(
            rows,
            resolved_filters,
        )

    if plan.column:
        resolved_column = resolve_column(
            parsed_workbook,
            plan.sheet,
            plan.column,
        )

        column = resolved_column["column"]

    else:
        column = None

    operation = plan.operation.lower()

    if operation == "count":
        return count(rows)

    if operation == "sum":
        if not column:
            raise ValueError(
                "Sum operation requires a column."
            )

        return sum_column(
            rows,
            column,
        )

    if operation == "average":
        if not column:
            raise ValueError(
                "Average operation requires a column."
            )

        return average(
            rows,
            column,
        )

    if operation == "minimum":
        if not column:
            raise ValueError(
                "Minimum operation requires a column."
            )

        return minimum(
            rows,
            column,
        )

    if operation == "maximum":
        if not column:
            raise ValueError(
                "Maximum operation requires a column."
            )

        return maximum(
            rows,
            column,
        )

    if operation == "search":
        if not column:
            raise ValueError(
                "Search operation requires a column."
            )

        if plan.query is None:
            raise ValueError(
                "Search operation requires a query."
            )

        return search(
            rows,
            column,
            plan.query,
        )

    if operation == "filter":

        if not plan.filters:
            raise ValueError(
                "Filter operation requires filters."
            )

        return filter_rows_multiple(
            rows,
            plan.filters,
        )

    if operation == "sort":
        if not column:
            raise ValueError(
                "Sort operation requires a column."
            )

        descending = False

        if plan.query:
            descending = (
                plan.query.lower()
                in {"desc", "descending"}
            )

        return sort_rows(
            rows,
            column,
            descending=descending,
        )

    raise ValueError(
        f"Unsupported operation: {plan.operation}"
    )