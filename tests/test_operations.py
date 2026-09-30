from parser.xlsx_parser import parse_xlsx
from executor.operations import (
    get_rows,
    count,
    sum_column,
    average,
    minimum,
    maximum,
    unique,
    search,
    filter_rows,
    sort_rows,
)


FILE_PATH = "data/uploads/eod.xlsx"


def get_test_rows():
    workbook = parse_xlsx(FILE_PATH)
    return get_rows(workbook)


def test_get_rows():
    rows = get_test_rows()

    assert len(rows) > 0


def test_count():
    rows = get_test_rows()

    result = count(rows)

    assert result == len(rows)


def test_unique():
    rows = get_test_rows()

    result = unique(rows, "C")

    assert isinstance(result, list)


def test_search():
    rows = get_test_rows()

    result = search(rows, "D", "RAG")

    assert isinstance(result, list)


def test_filter_rows():
    rows = get_test_rows()

    result = filter_rows(
        rows,
        "A",
        ">",
        2,
    )

    assert isinstance(result, list)

    for row in result:
        value = row["cells"]["A" + str(row["row"])]["value"]
        assert value > 2


def test_sort_rows():
    rows = get_test_rows()

    result = sort_rows(
        rows,
        "A",
    )

    assert isinstance(result, list)


def test_sum_column():
    rows = get_test_rows()

    result = sum_column(rows, "A")

    assert isinstance(result, (int, float))


def test_average():
    rows = get_test_rows()

    result = average(rows, "A")

    assert isinstance(result, (int, float))


def test_minimum():
    rows = get_test_rows()

    result = minimum(rows, "A")

    assert isinstance(result, (int, float))


def test_maximum():
    rows = get_test_rows()

    result = maximum(rows, "A")

    assert isinstance(result, (int, float))