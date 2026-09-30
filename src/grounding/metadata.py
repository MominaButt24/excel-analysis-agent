# from openpyxl import load_workbook
# from openpyxl.utils import get_column_letter


# def is_empty_row(values):
#     return all(value is None for value in values)


# def get_row_values(worksheet, row_number):
#     return [
#         worksheet.cell(
#             row=row_number,
#             column=column_number,
#         ).value
#         for column_number in range(
#             1,
#             worksheet.max_column + 1,
#         )
#     ]


# def find_header_rows(worksheet):
#     """
#     Find rows that look like table headers.

#     A header row usually contains at least
#     two text values.
#     """
#     header_rows = []

#     for row_number in range(
#         1,
#         worksheet.max_row + 1,
#     ):
#         values = get_row_values(
#             worksheet,
#             row_number,
#         )

#         text_values = [
#             value
#             for value in values
#             if isinstance(value, str)
#             and value.strip()
#         ]

#         if len(text_values) >= 2:
#             header_rows.append(row_number)

#     return header_rows


# def get_columns(worksheet, header_row):
#     columns = []

#     for column_number in range(
#         1,
#         worksheet.max_column + 1,
#     ):
#         value = worksheet.cell(
#             row=header_row,
#             column=column_number,
#         ).value

#         if value is None:
#             continue

#         columns.append({
#             "name": str(value).strip(),
#             "column": get_column_letter(
#                 column_number
#             ),
#             "coordinate": (
#                 f"{get_column_letter(column_number)}"
#                 f"{header_row}"
#             ),
#         })

#     return columns


# def get_parent_headers(
#     worksheet,
#     header_row,
# ):
#     """
#     Detect merged horizontal headers above
#     the actual column headers.
#     """
#     parent_headers = {}

#     for merged_range in worksheet.merged_cells.ranges:

#         min_col = merged_range.min_col
#         max_col = merged_range.max_col
#         min_row = merged_range.min_row
#         max_row = merged_range.max_row

#         # We only care about horizontal merged
#         # cells above the actual header row.
#         if (
#             min_row >= header_row
#             or max_row >= header_row
#             or min_col == max_col
#         ):
#             continue

#         value = worksheet.cell(
#             row=min_row,
#             column=min_col,
#         ).value

#         if value is None:
#             continue

#         columns = [
#             get_column_letter(column)
#             for column in range(
#                 min_col,
#                 max_col + 1,
#             )
#         ]

#         parent_headers[str(value).strip()] = columns

#     return parent_headers


# def get_row_groups(
#     worksheet,
#     header_row,
# ):
#     """
#     Detect vertically merged cells below
#     the header row.

#     Example:

#     A6:A10 = Electronics
#     """
#     groups = []

#     for merged_range in worksheet.merged_cells.ranges:

#         min_col = merged_range.min_col
#         max_col = merged_range.max_col
#         min_row = merged_range.min_row
#         max_row = merged_range.max_row

#         # Only vertical merges.
#         if (
#             min_col != max_col
#             or min_row <= header_row
#             or min_row == max_row
#         ):
#             continue

#         value = worksheet.cell(
#             row=min_row,
#             column=min_col,
#         ).value

#         if value is None:
#             continue

#         groups.append({
#             "label": str(value).strip(),
#             "column": get_column_letter(
#                 min_col
#             ),
#             "range": f"{min_row}:{max_row}",
#         })

#     return groups


# def get_special_rows(
#     worksheet,
#     header_row,
# ):
#     """
#     Detect obvious total/subtotal/note rows.
#     """
#     special_rows = []

#     for row_number in range(
#         header_row + 1,
#         worksheet.max_row + 1,
#     ):
#         values = get_row_values(
#             worksheet,
#             row_number,
#         )

#         text = " ".join(
#             str(value).lower()
#             for value in values
#             if isinstance(value, str)
#         )

#         if "grand total" in text:
#             special_rows.append({
#                 "row": row_number,
#                 "type": "grand_total",
#             })

#         elif "subtotal" in text:
#             special_rows.append({
#                 "row": row_number,
#                 "type": "subtotal",
#             })

#         elif "note" in text:
#             special_rows.append({
#                 "row": row_number,
#                 "type": "note",
#             })

#     return special_rows


# def build_sheet_metadata(worksheet):
#     header_rows = find_header_rows(
#         worksheet
#     )

#     if not header_rows:
#         return {
#             "sheet": worksheet.title,
#             "dimensions": {
#                 "rows": worksheet.max_row,
#                 "columns": worksheet.max_column,
#             },
#             "blocks": [],
#         }

#     # For now, use the first detected header row.
#     header_row = header_rows[0]

#     columns = get_columns(
#         worksheet,
#         header_row,
#     )

#     return {
#         "sheet": worksheet.title,

#         "dimensions": {
#             "rows": worksheet.max_row,
#             "columns": worksheet.max_column,
#         },

#         "header_row": header_row,

#         "columns": columns,

#         "parent_headers": get_parent_headers(
#             worksheet,
#             header_row,
#         ),

#         "row_groups": get_row_groups(
#             worksheet,
#             header_row,
#         ),

#         "special_rows": get_special_rows(
#             worksheet,
#             header_row,
#         ),

#         "merged_ranges": [
#             str(merged_range)
#             for merged_range
#             in worksheet.merged_cells.ranges
#         ],
#     }


# def build_workbook_metadata(file_path):
#     workbook = load_workbook(
#         file_path,
#         data_only=True,
#     )

#     return {
#         "file": file_path,

#         "sheets": [
#             build_sheet_metadata(
#                 worksheet
#             )
#             for worksheet in workbook.worksheets
#         ],
#     }

def column_letter(coordinate):
    """
    Extract column letter from a cell coordinate.

    Example:
        A5 -> A
        AA10 -> AA
    """
    return "".join(
        character
        for character in coordinate
        if character.isalpha()
    )


def build_sheet_metadata(sheet):
    columns = []

    for column in sheet["columns"]:
        coordinate = column["coordinate"]

        columns.append({
            "name": column["name"],
            "column": column_letter(coordinate),
        })

    return {
        "name": sheet["name"],
        "dimensions": sheet["dimensions"],
        "header_row": sheet["actual_header_row"],
        "columns": columns,
        "blocks": [
            {
                "block_id": block["block_id"],
                "rows": [
                    row["row"]
                    for row in block["rows"]
                ],
            }
            for block in sheet["blocks"]
        ],
    }


def build_workbook_metadata(parsed_workbook):
    """
    Build compact metadata from the parsed workbook.

    This function does NOT read the XLSX file.
    The parser is responsible for reading the workbook.
    """

    return {
        "file": parsed_workbook["file"],
        "sheets": [
            build_sheet_metadata(sheet)
            for sheet in parsed_workbook["sheets"]
        ],
    }