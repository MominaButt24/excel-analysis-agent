from parser.xlsx_parser import parse_xlsx
from executor.plan import ExecutionPlan
from executor.executor import execute_plan, get_sheet_rows
from executor.operations import minimum, sum_column


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

    assert result == 18


def test_sum_inventory_excludes_grand_total_row():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    plan = ExecutionPlan(
        sheet="Inventory",
        operation="sum",
        column="Total Value",
    )

    result = execute_plan(
        parsed,
        plan,
    )

    assert result == 31714.82


def test_clean_baseline_count_and_quantity_sum():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    count_plan = ExecutionPlan(
        sheet="Clean_Baseline",
        operation="count",
    )
    quantity_sum_plan = ExecutionPlan(
        sheet="Clean_Baseline",
        operation="sum",
        column="Qty",
    )

    assert execute_plan(parsed, count_plan) == 6
    assert execute_plan(parsed, quantity_sum_plan) == 2587


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


def test_count_present_employees_on_day_first_date():
    parsed = {
        "sheets": [{
            "name": "Daily Summary",
            "columns": [
                {
                    "name": "Employee",
                    "coordinate": "A1",
                    "field_id": "A",
                },
                {
                    "name": "Date",
                    "coordinate": "C1",
                    "field_id": "C",
                },
                {
                    "name": "Status",
                    "coordinate": "D1",
                    "field_id": "D",
                },
            ],
            "blocks": [{
                "block_id": 1,
                "rows": [
                    {
                        "row": 2,
                        "kind": "data",
                        "values": {
                            "A": "Asha",
                            "C": "2026-08-20",
                            "D": "Present",
                        },
                        "cells": {},
                    },
                    {
                        "row": 3,
                        "kind": "data",
                        "values": {
                            "A": "Bilal",
                            "C": "2026-08-20",
                            "D": "Absent",
                        },
                        "cells": {},
                    },
                    {
                        "row": 4,
                        "kind": "data",
                        "values": {
                            "A": "Chen",
                            "C": "2026-08-21",
                            "D": "Present",
                        },
                        "cells": {},
                    },
                ],
            }],
        }],
    }
    plan = ExecutionPlan(
        sheet="Daily Summary",
        operation="count",
        filters=[
            {
                "column": "Date",
                "operator": "==",
                "value": "20-08-2026",
            },
            {
                "column": "Status",
                "operator": "==",
                "value": "Present",
            },
        ],
    )

    assert execute_plan(parsed, plan) == 1


def test_eod_count_skips_month_headers_and_leave_rows():
    parsed = parse_xlsx("data/uploads/eod.xlsx")
    momna = next(
        sheet
        for sheet in parsed["sheets"]
        if sheet["name"] == "Momna"
    )

    assert len(get_sheet_rows(momna)) == 35


def test_eod_fine_sum_extracts_currency_amounts_from_text():
    parsed = parse_xlsx("data/uploads/eod.xlsx")
    momna = next(
        sheet
        for sheet in parsed["sheets"]
        if sheet["name"] == "Momna"
    )
    rows = get_sheet_rows(momna)
    fine_row = next(row for row in rows if row["row"] == 25)

    assert sum_column(rows, "H") == 400
    assert fine_row["cells"]["H25"]["value"] == "Missing EOD FIne RS 200"


def test_eod_earliest_record_date_is_iso_date():
    parsed = parse_xlsx("data/uploads/eod.xlsx")
    momna = next(
        sheet
        for sheet in parsed["sheets"]
        if sheet["name"] == "Momna"
    )

    assert minimum(get_sheet_rows(momna), "B") == "2026-08-12"