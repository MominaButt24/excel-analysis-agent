from parser.xlsx_parser import parse_xlsx


file_path = "data/uploads/eod.xlsx"
file_path = "data/uploads/inventory_parser_test.xlsx"

workbook = parse_xlsx(file_path)

print("\n" + "=" * 70)
print("XLSX PARSER RESULT")
print("=" * 70)

print(f"Sheets: {len(workbook['sheets'])}")

for sheet in workbook["sheets"]:

    print("\n" + "-" * 70)
    print(f"SHEET: {sheet['name']}")
    print("-" * 70)

    dimensions = sheet["dimensions"]

    print(
        f"Dimensions: "
        f"{dimensions['rows']} rows × "
        f"{dimensions['columns']} columns"
    )

    print(f"Header row: {sheet['header_row']}")

    print("\nColumns:")

    for column in sheet["columns"]:
        print(
            f"  {column['coordinate']}: "
            f"{column['name']}"
        )

    print(
        f"\nMerged ranges: "
        f"{sheet['merged_ranges']}"
    )

    print(
        f"Blocks detected: "
        f"{len(sheet['blocks'])}"
    )

    for block in sheet["blocks"]:

        print(
            f"\n  BLOCK {block['block_id']}"
        )

        print(
            f"  Rows: {len(block['rows'])}"
        )

        print("  First 20 rows:")

        for row in block["rows"][:20]:
            print(f"    {row}")