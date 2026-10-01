import pytest

from executor.plan import ExecutionPlan
from validator.validator import validate_result


def test_validate_numeric_result():

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="average",
        column="Unit Cost",
    )

    assert validate_result(
        42.5,
        plan,
    )


def test_validate_list_result():

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="search",
        column="Product Name",
        query="Mouse",
    )

    assert validate_result(
        [{"row": 1}],
        plan,
    )


def test_reject_invalid_numeric_result():

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="sum",
        column="Total Value",
    )

    with pytest.raises(ValueError):

        validate_result(
            "not a number",
            plan,
        )