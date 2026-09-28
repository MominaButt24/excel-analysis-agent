from parser.xlsx_parser import parse_xlsx


file_path = "data/uploads/eod.xlsx"

sheets = parse_xlsx(file_path)

for sheet_name, df in sheets.items():
    print(f"\n--- {sheet_name} ---")
    print(f"Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(df.head())