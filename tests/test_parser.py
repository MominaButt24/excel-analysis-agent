from parser.xlsx_parser import parse_xlsx


FILE_PATH = "data/uploads/eod.xlsx"


def test_workbook_has_sheets():
    workbook = parse_xlsx(FILE_PATH)

    assert "sheets" in workbook
    assert len(workbook["sheets"]) > 0


def test_sheet_has_structure():
    workbook = parse_xlsx(FILE_PATH)

    for sheet in workbook["sheets"]:
        assert "name" in sheet
        assert "dimensions" in sheet
        assert "header_row" in sheet
        assert "columns" in sheet
        assert "merged_ranges" in sheet
        assert "blocks" in sheet


def test_columns_have_structure():
    workbook = parse_xlsx(FILE_PATH)

    for sheet in workbook["sheets"]:
        for column in sheet["columns"]:
            assert "index" in column
            assert "name" in column
            assert "coordinate" in column


def test_rows_preserve_coordinates():
    workbook = parse_xlsx(FILE_PATH)

    for sheet in workbook["sheets"]:
        for block in sheet["blocks"]:
            for row in block["rows"]:
                assert "sheet" in row
                assert "row" in row
                assert "cells" in row

                for coordinate, cell in row["cells"].items():
                    assert coordinate
                    assert "column" in cell
                    assert "value" in cell


def test_eod_date_is_normalized():
    workbook = parse_xlsx(FILE_PATH)

    momna = next(
        sheet
        for sheet in workbook["sheets"]
        if sheet["name"] == "Momna"
    )

    first_block = momna["blocks"][0]

    row_3 = next(
        row
        for row in first_block["rows"]
        if row["row"] == 3
    )

    assert row_3["cells"]["B3"]["value"] == "2026-08-12"


def test_merged_ranges_are_preserved():
    workbook = parse_xlsx(FILE_PATH)

    momna = next(
        sheet
        for sheet in workbook["sheets"]
        if sheet["name"] == "Momna"
    )

    assert "A2:H2" in momna["merged_ranges"]