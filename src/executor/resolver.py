import re


def normalize_name(value):
    if value is None:
        return None

    return " ".join(
        str(value).strip().lower().split()
    )


def resolve_column(
    parsed_workbook,
    sheet_name,
    column_name,
):
    """
    Resolve a human-readable column name
    to its Excel column letter.
    """

    target = normalize_name(column_name)

    for sheet in parsed_workbook["sheets"]:

        if normalize_name(sheet["name"]) != normalize_name(
            sheet_name
        ):
            continue

        matches = []

        for column in sheet["columns"]:

            header = normalize_name(
                column["name"]
            )

            if header != target:
                continue

            coordinate = column["coordinate"]

            column_letter = re.match(
                r"[A-Z]+",
                coordinate
            ).group()

            matches.append({
                "column": column_letter,
                "header": column["name"],
                "coordinate": coordinate,
            })

        if not matches:
            raise ValueError(
                f"Column '{column_name}' "
                f"not found in sheet '{sheet_name}'."
            )

        if len(matches) > 1:
            raise ValueError(
                f"Column '{column_name}' is ambiguous "
                f"in sheet '{sheet_name}': {matches}"
            )

        return matches[0]

    raise ValueError(
        f"Sheet '{sheet_name}' not found."
    )

def resolve_plan_columns(
    parsed_workbook,
    plan,
):
    """
    Resolve and validate every column referenced
    by an ExecutionPlan.
    """

    resolved = {}

    if plan.column:
        resolved["column"] = resolve_column(
            parsed_workbook,
            plan.sheet,
            plan.column,
        )

    if plan.filters:

        resolved_filters = []

        for condition in plan.filters:

            column = resolve_column(
                parsed_workbook,
                plan.sheet,
                condition["column"],
            )

            resolved_condition = {
                **condition,
                "column": column["column"],
            }

            if "value_from_column" in condition:

                comparison_column = resolve_column(
                    parsed_workbook,
                    plan.sheet,
                    condition[
                        "value_from_column"
                    ],
                )

                resolved_condition[
                    "value_from_column"
                ] = comparison_column["column"]

            resolved_filters.append(
                resolved_condition
            )

        resolved["filters"] = resolved_filters

    return resolved