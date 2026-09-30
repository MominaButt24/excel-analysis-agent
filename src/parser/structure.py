def get_row_values(worksheet, row_number):
    return [
        worksheet.cell(
            row=row_number,
            column=column_number
        ).value
        for column_number in range(
            1,
            worksheet.max_column + 1
        )
    ]


def is_empty_row(values):
    return all(
        value is None
        for value in values
    )


def get_text_values(values):
    return [
        value
        for value in values
        if isinstance(value, str)
        and value.strip()
    ]


def detect_header_row(worksheet):
    """
    Find the first row that looks like a table header.
    """

    for row_number in range(
        1,
        worksheet.max_row + 1
    ):

        values = get_row_values(
            worksheet,
            row_number
        )

        text_values = get_text_values(values)

        if len(text_values) >= 2:
            return row_number

    return None


def detect_actual_header_row(
    worksheet,
    header_row,
):
    """
    Detect whether the first detected header row
    is a parent/group header with the actual column
    headers on the following row.

    Example:

        Row 4:
        Item Details | ... | Stock Levels

        Row 5:
        Category | SKU | Product Name | Qty On Hand

    Returns:
        5

    For a normal sheet where row 1 already contains
    the actual headers, returns 1.
    """

    if header_row is None:
        return None

    if header_row >= worksheet.max_row:
        return header_row

    current_values = get_row_values(
        worksheet,
        header_row
    )

    next_values = get_row_values(
        worksheet,
        header_row + 1
    )

    # If the current header row contains horizontal
    # merged ranges, it is likely a parent header.
    has_horizontal_merge = False

    for merged_range in worksheet.merged_cells.ranges:

        if merged_range.min_row != header_row:
            continue

        if merged_range.max_row != header_row:
            continue

        if merged_range.min_col == merged_range.max_col:
            continue

        has_horizontal_merge = True
        break

    if not has_horizontal_merge:
        return header_row

    current_text_count = len(
        get_text_values(current_values)
    )

    next_text_count = len(
        get_text_values(next_values)
    )

    if next_text_count >= current_text_count:
        return header_row + 1

    return header_row


def detect_active_columns(
    worksheet,
    start_row=1,
):
    """
    Ignore Excel's formatting-only columns.
    """

    active_columns = []

    for column_number in range(
        1,
        worksheet.max_column + 1
    ):

        has_value = False

        for row_number in range(
            start_row,
            worksheet.max_row + 1
        ):

            if worksheet.cell(
                row=row_number,
                column=column_number
            ).value is not None:

                has_value = True
                break

        if has_value:
            active_columns.append(
                column_number
            )

    return active_columns


def detect_parent_headers(
    worksheet,
    parent_header_row,
    actual_header_row,
):
    """
    Extract horizontal merged headers and map them
    to their child columns.

    Example:

        A4:C4 = Item Details

    becomes:

        Item Details -> A, B, C
    """

    if (
        parent_header_row is None
        or actual_header_row is None
        or parent_header_row == actual_header_row
    ):
        return {}

    parent_headers = {}

    for merged_range in worksheet.merged_cells.ranges:

        if merged_range.min_row != parent_header_row:
            continue

        if merged_range.max_row != parent_header_row:
            continue

        if merged_range.min_col == merged_range.max_col:
            continue

        value = worksheet.cell(
            row=parent_header_row,
            column=merged_range.min_col
        ).value

        if value is None:
            continue

        columns = []

        for column_number in range(
            merged_range.min_col,
            merged_range.max_col + 1
        ):
            columns.append(column_number)

        parent_headers[str(value).strip()] = columns

    return parent_headers


def detect_blocks(
    worksheet,
    start_row,
):
    """
    Detect blocks separated by completely empty rows.
    """

    blocks = []
    current_rows = []

    for row_number in range(
        start_row,
        worksheet.max_row + 1
    ):

        values = get_row_values(
            worksheet,
            row_number
        )

        empty = is_empty_row(values)

        if empty:

            if current_rows:
                blocks.append(current_rows)
                current_rows = []

            continue

        current_rows.append(row_number)

    if current_rows:
        blocks.append(current_rows)

    return blocks