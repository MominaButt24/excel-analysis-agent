from parser.xlsx_parser import parse_xlsx
from grounding.metadata import build_workbook_metadata


def test_build_workbook_metadata():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    metadata = build_workbook_metadata(parsed)

    assert metadata["sheets"]

    inventory = metadata["sheets"][0]

    assert inventory["name"] == "Inventory"

    assert inventory["header_row"] == 5

    column_names = [
        column["name"]
        for column in inventory["columns"]
    ]

    assert "Category" in column_names
    assert "SKU" in column_names
    assert "Status" in column_names


def test_metadata_disambiguates_duplicate_headers():
    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )
    metadata = build_workbook_metadata(parsed)
    edge_cases = next(
        sheet
        for sheet in metadata["sheets"]
        if sheet["name"] == "Messy_EdgeCases"
    )
    quantity_columns = [
        column
        for column in edge_cases["columns"]
        if column["name"] == "Qty"
    ]

    assert [column["field_id"] for column in quantity_columns] == [
        "C",
        "D",
    ]
    assert all(
        column["inferred_type"] == "number"
        for column in quantity_columns
    )