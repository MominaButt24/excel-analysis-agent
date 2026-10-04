import re

from executor.resolver import resolve_column


_FILTERABLE_HEADER_TERMS = {
    "category",
    "class",
    "department",
    "group",
    "segment",
    "status",
    "type",
}


def normalize_value_tokens(value):
    tokens = re.findall(r"[^\W_]+", str(value).casefold())
    normalized = []

    for token in tokens:
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif (
            len(token) > 3
            and token.endswith("s")
            and not token.endswith(("ss", "us", "is"))
        ):
            token = token[:-1]

        normalized.append(token)

    return tuple(normalized)


def _contains_phrase(text_tokens, phrase_tokens):
    if not phrase_tokens or len(phrase_tokens) > len(text_tokens):
        return False

    return any(
        text_tokens[index:index + len(phrase_tokens)] == phrase_tokens
        for index in range(len(text_tokens) - len(phrase_tokens) + 1)
    )


def ground_categorical_filters(parsed_workbook, query, plan):
    """Add exact workbook values mentioned with singular/plural variation."""
    sheet = next(
        (
            candidate
            for candidate in parsed_workbook["sheets"]
            if candidate["name"].strip().casefold()
            == plan.sheet.strip().casefold()
        ),
        None,
    )
    if sheet is None:
        return plan

    query_tokens = normalize_value_tokens(query)
    plan.filters = list(plan.filters or [])

    for column in sheet["columns"]:
        header_tokens = set(
            normalize_value_tokens(column.get("name") or "")
        )
        if not header_tokens.intersection(_FILTERABLE_HEADER_TERMS):
            continue

        candidates = {
            row.get("values", {}).get(column["field_id"])
            for block in sheet["blocks"]
            for row in block["rows"]
            if row.get("kind", "data") == "data"
            and isinstance(
                row.get("values", {}).get(column["field_id"]),
                str,
            )
        }
        matches = [
            value
            for value in candidates
            if _contains_phrase(
                query_tokens,
                normalize_value_tokens(value),
            )
        ]

        if len(matches) != 1:
            continue

        field_id = column["field_id"]
        existing_filter = None
        for condition in plan.filters:
            try:
                existing_column = resolve_column(
                    parsed_workbook,
                    plan.sheet,
                    condition["column"],
                )["column"]
            except ValueError:
                continue

            if existing_column == field_id:
                existing_filter = condition
                break

        if existing_filter is None:
            plan.filters.append({
                "column": field_id,
                "operator": "==",
                "value": matches[0],
            })
        elif (
            existing_filter.get("operator") in {"=", "=="}
            and "value" in existing_filter
            and normalize_value_tokens(existing_filter["value"])
            == normalize_value_tokens(matches[0])
        ):
            existing_filter["value"] = matches[0]

    if not plan.filters:
        plan.filters = None

    return plan