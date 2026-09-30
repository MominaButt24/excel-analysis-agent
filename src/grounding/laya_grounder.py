from laya import Router


router = Router()


def evaluate_with_laya(
    query: str,
    metadata: dict,
):
    state = build_laya_state(
        query,
        metadata,
    )

    questions = build_questions(metadata)

    return router.predict(
        state,
        questions,
    )


def build_laya_state(
    query: str,
    metadata: dict,
):
    lines = [
        f"USER QUERY:\n{query}",
        "",
        "WORKBOOK:",
    ]

    for sheet in metadata["sheets"]:
        lines.append(
            f"\nSheet: {sheet['name']}"
        )

        lines.append(
            f"Header row: {sheet['header_row']}"
        )

        lines.append("Columns:")

        for column in sheet["columns"]:
            lines.append(
                f"{column['column']} = "
                f"{column['name']}"
            )

        if sheet["blocks"]:
            lines.append("Blocks:")

            for block in sheet["blocks"]:
                lines.append(
                    f"Block {block['block_id']}: "
                    f"rows {block['rows']}"
                )

    return "\n".join(lines)

def build_questions(metadata):

    sheet_choices = {
        sheet["name"]: (
            f"The {sheet['name']} worksheet "
            "contains relevant data."
        )
        for sheet in metadata["sheets"]
    }

    return {
        "intent": {
            "type": "choice",
            "instructions": (
                "What operation does the user "
                "want to perform?"
            ),
            "criteria": {
                "count": "Count matching rows or values.",
                "sum": "Calculate a total.",
                "average": "Calculate an average.",
                "filter": "Find rows matching a condition.",
                "search": "Find specific data.",
                "sort": "Sort rows.",
                "unknown": "The operation is unclear.",
            },
        },
        "sheet": {
            "type": "choice",
            "instructions": (
                "Which worksheet contains the "
                "information needed to answer "
                "the user's query?"
            ),
            "criteria": sheet_choices,
        },

        "query_complete": {
            "type": "noul",
            "instructions": (
                "Is the user's query specific enough "
                "to identify the required spreadsheet "
                "data without clarification?"
            ),
        },
    }

# def build_questions(metadata):
#     sheet_choices = {
#         sheet["name"]: (
#             f"The {sheet['name']} worksheet "
#             "contains relevant data."
#         )
#         for sheet in metadata["sheets"]
#     }

#     return {
#         "intent": {
#             "type": "choice",
#             "instructions": (
#                 "What operation does the user "
#                 "want to perform?"
#             ),
#             "criteria": {
#                 "count": "Count matching rows or values.",
#                 "sum": "Calculate a total.",
#                 "average": "Calculate an average.",
#                 "filter": "Find rows matching a condition.",
#                 "search": "Find specific data.",
#                 "sort": "Sort rows.",
#                 "unknown": "The operation is unclear.",
#             },
#         },

#         "sheet": {
#             "type": "choice",
#             "instructions": (
#                 "Which worksheet contains the data "
#                 "needed to answer the query?"
#             ),
#             "criteria": sheet_choices,
#         },

#         "query_complete": {
#             "type": "noul",
#             "instructions": (
#                 "Is the user's query specific enough "
#                 "to execute without clarification?"
#             ),
#         },
#     }