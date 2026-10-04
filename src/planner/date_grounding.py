import re


JOIN_DATE_QUERY = re.compile(
    r"\b(joining|joined|hire|hired|employment start|start date)\b",
    re.IGNORECASE,
)


def ground_join_date_query(parsed_workbook, query, plan):
    """Route join-date questions to an explicit date field or earliest log date."""
    if not JOIN_DATE_QUERY.search(query):
        return False

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
        return False

    explicit_date_columns = []
    date_columns = []

    for column in sheet["columns"]:
        name = str(column.get("name") or "").strip().casefold()
        if "date" not in name:
            continue
        date_columns.append(column)
        if any(term in name for term in ("joining", "joined", "hire", "start")):
            explicit_date_columns.append(column)

    candidates = explicit_date_columns or date_columns
    if not candidates:
        return False

    plan.operation = "minimum"
    plan.column = candidates[0].get("field_id") or candidates[0]["name"]
    plan.filters = None
    return not explicit_date_columns