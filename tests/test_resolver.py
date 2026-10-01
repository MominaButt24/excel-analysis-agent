from parser.xlsx_parser import parse_xlsx
from executor.resolver import resolve_column

from executor.plan import ExecutionPlan
from executor.resolver import resolve_plan_columns
from parser.xlsx_parser import parse_xlsx

FILE_PATH = "data/uploads/eod.xlsx"

def test_resolve_filter_columns():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="filter",
        filters=[
            {
                "column": "Category",
                "operator": "==",
                "value": "Electronics",
            },
            {
                "column": "Qty On Hand",
                "operator": "<",
                "value_from_column": "Reorder Level",
            },
        ],
    )

    resolved = resolve_plan_columns(
        parsed,
        plan,
    )

    assert resolved["filters"][0]["column"] == "A"

    assert (
        resolved["filters"][1]["column"]
        == "D"
    )

    assert (
        resolved["filters"][1]["value_from_column"]
        == "E"
    )

def get_workbook():
    return parse_xlsx(FILE_PATH)


def test_resolve_column():
    workbook = get_workbook()

    result = resolve_column(
        workbook,
        "Momna",
        "Fine",
    )

    assert result["column"] == "H"
    assert result["header"] == "Fine"
    assert result["coordinate"] == "H1"


def test_resolve_column_case_insensitive():
    workbook = get_workbook()

    result = resolve_column(
        workbook,
        "momna",
        "fine",
    )

    assert result["column"] == "H"


def test_missing_column():
    workbook = get_workbook()

    try:
        resolve_column(
            workbook,
            "Momna",
            "Does Not Exist",
        )
        assert False
    except ValueError as error:
        assert "not found" in str(error)


def test_missing_sheet():
    workbook = get_workbook()

    try:
        resolve_column(
            workbook,
            "Unknown Sheet",
            "Fine",
        )
        assert False
    except ValueError as error:
        assert "not found" in str(error)