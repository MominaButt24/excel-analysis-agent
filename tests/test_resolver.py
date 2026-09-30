from parser.xlsx_parser import parse_xlsx
from executor.resolver import resolve_column


FILE_PATH = "data/uploads/eod.xlsx"


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