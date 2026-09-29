from parser.xlsx_parser import parse_xlsx


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

    print(
        f"Dimensions: "
        f"{sheet['dimensions']['max_row']} rows × "
        f"{sheet['dimensions']['max_column']} columns"
    )

    print(f"Header row: {sheet['header_row']}")

    print("\nColumns:")

    for column in sheet["columns"]:
        print(
            f"  {column['index']}: "
            f"{column['name']}"
        )

    print(f"\nData rows: {len(sheet['rows'])}")

    print("\nFirst 5 rows:")

    for row in sheet["rows"][:5]:

        print(
            f"  Row {row['row_number']}: "
            f"{row['values']}"
        )