from parser.xlsx_parser import parse_xlsx
from executor.executor import execute_plan
from executor.plan import ExecutionPlan
from planner.value_grounding import ground_categorical_filters


WORKBOOK_PATH = "data/uploads/inventory_parser_test.xlsx"


def test_ground_singular_category_to_canonical_plural_value():
    parsed = parse_xlsx(WORKBOOK_PATH)
    plan = ExecutionPlan(
        sheet="Inventory",
        operation="count",
    )

    ground_categorical_filters(
        parsed,
        "how many electronic products are there?",
        plan,
    )

    assert plan.filters == [{
        "column": "A",
        "operator": "==",
        "value": "Electronics",
    }]
    assert execute_plan(parsed, plan) == 5


def test_ground_category_for_list_request():
    parsed = parse_xlsx(WORKBOOK_PATH)
    plan = ExecutionPlan(
        sheet="Inventory",
        operation="filter",
    )

    ground_categorical_filters(
        parsed,
        "list all electronics products",
        plan,
    )

    rows = execute_plan(parsed, plan)

    assert len(rows) == 5
    assert all(row["values"]["A"] == "Electronics" for row in rows)