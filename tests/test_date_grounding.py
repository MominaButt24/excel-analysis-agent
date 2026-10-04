from executor.executor import execute_plan
from executor.plan import ExecutionPlan
from parser.xlsx_parser import parse_xlsx
from planner.date_grounding import ground_join_date_query


def test_join_date_query_uses_earliest_date_with_caveat():
    parsed = parse_xlsx("data/uploads/eod.xlsx")
    plan = ExecutionPlan(
        sheet="Momna",
        operation="minimum",
        column="Fine",
    )

    is_estimate = ground_join_date_query(
        parsed,
        "What is the joining date of Momna?",
        plan,
    )

    assert is_estimate is True
    assert plan.operation == "minimum"
    assert plan.column == "B"
    assert execute_plan(parsed, plan) == "2026-08-12"