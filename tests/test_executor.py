from parser.xlsx_parser import parse_xlsx
from executor.plan import ExecutionPlan
from executor.executor import execute_plan


def test_count_inventory_rows():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="count",
    )

    result = execute_plan(
        parsed,
        plan,
    )

    assert result == 20


def test_average_unit_cost():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="average",
        column="Unit Cost",
    )

    result = execute_plan(
        parsed,
        plan,
    )

    assert result is not None


def test_search_product():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="search",
        column="Product Name",
        query="Mechanical Keyboard",
    )

    result = execute_plan(
        parsed,
        plan,
    )

    assert len(result) == 1

def test_multiple_filters_with_column_comparison():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="filter",
        filters=[
            {
                "column": "A",
                "operator": "==",
                "value": "Electronics",
            },
            {
                "column": "D",
                "operator": "<",
                "value_from_column": "E",
            },
        ],
    )

    result = execute_plan(
        parsed,
        plan,
    )

    assert len(result) == 2