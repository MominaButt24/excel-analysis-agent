from parser.xlsx_parser import parse_xlsx
from grounding.metadata import build_workbook_metadata
from grounding.laya_grounder import evaluate_with_laya


def test_laya_excel_queries():

    parsed = parse_xlsx(
        "data/uploads/inventory_parser_test.xlsx"
    )

    metadata = build_workbook_metadata(
        parsed
    )

    queries = [
        "How many electronics items are below the reorder level?",
        "What is the total value of all inventory?",
        "Which products are out of stock?",
        "What is the average unit cost?",
        "Find the Mechanical Keyboard.",
        "Which sheet contains supplier contacts?",
    ]

    for query in queries:

        print("\n" + "=" * 60)
        print("QUERY:", query)

        result = evaluate_with_laya(
            query=query,
            metadata=metadata,
        )

        print("RESULT:")
        print(result["answers"])