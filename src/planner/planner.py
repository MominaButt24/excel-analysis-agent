from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator
from langchain_cerebras import ChatCerebras
from src.llm.model import get_langfuse_handler
from src.config.llm_config import llm_config
from executor.plan import ExecutionPlan


class FilterCondition(BaseModel):
    column: str

    operator: Literal[
        "==",
        "=",
        "!=",
        ">",
        "<",
        ">=",
        "<=",
    ]

    value: Any | None = None
    value_from_column: str | None = None


class LLMExecutionPlan(BaseModel):
    sheet: str
    operation: Literal[
        "count",
        "sum",
        "average",
        "minimum",
        "maximum",
        "search",
        "filter",
        "sort",
    ]
    column: str | None = None
    filters: list[FilterCondition] | None = None
    query: str | None = None

    @field_validator(
        "filters",
        mode="before",
    )
    @classmethod
    def normalize_filters(cls, value):

        if value is None:
            return None

        if isinstance(value, list):
            return value

        if isinstance(value, dict):

            normalized = []

            for column, condition in value.items():

                if isinstance(condition, dict):

                    normalized.append({
                        "column": column,
                        **condition,
                    })

            return normalized

        return value


def create_planner():
    cfg = llm_config()

    llm = ChatCerebras(
        model=cfg["model"],
        api_key=cfg["api_key"],
        max_tokens=cfg["max_tokens"],
        timeout=cfg["timeout"],
        max_retries=cfg["max_retries"],
    )

    return llm.with_structured_output(
        LLMExecutionPlan
    )


def build_planner_prompt(
    query: str,
    metadata: dict,
) -> str:

    return f"""
You are an Excel query planner.

Your job is to convert a user's natural-language
question into a structured execution plan.

You MUST only reference sheets and columns that
exist in the provided workbook metadata.

When a header name is duplicated, use its field_id
to identify the intended column. For example, use
"C" rather than "Qty" when metadata shows two
columns named "Qty" with field_ids "C" and "D".

Do not calculate any values yourself.

Choose the operation that best matches the user's
request.

Available operations:
- count
- sum
- average
- minimum
- maximum
- search
- filter
- sort

For questions asking "how many" or "how much", use count or an aggregate
operation instead of search. For attendance questions asking how many employees
were present on a date, use count with filters for the date and the presence
status. Do not use search as a substitute for counting matching records.

For "list", "show", or "which products/records" requests, use filter and
include every condition stated by the user. A filter plan with no conditions
means return all data rows from the selected sheet. If the query names a
category using a singular/plural variation, select the matching canonical
category value shown in workbook data.

For comparisons between two spreadsheet columns,
use value_from_column.

Example:
If the user asks for rows where Qty On Hand is
below Reorder Level:

column = "Qty On Hand"
operator = "<"
value_from_column = "Reorder Level"

WORKBOOK METADATA:
{metadata}

USER QUERY:
{query}
"""


def create_execution_plan(
    query: str,
    metadata: dict,
) -> ExecutionPlan:

    planner = create_planner()

    prompt = build_planner_prompt(
        query,
        metadata,
    )

    # llm_plan = planner.invoke(prompt)
    langfuse_handler = get_langfuse_handler()

    llm_plan = planner.invoke(
        prompt,
        config={
            "callbacks": [langfuse_handler],
            "metadata": {
                "langfuse_tags": [
                    "excel-analysis",
                    "planner",
                ]
            },
        },
    )

    filters = None

    if llm_plan.filters:
        filters = []

        for filter_condition in llm_plan.filters:

            condition = filter_condition.model_dump(
                exclude_none=True
            )

            if condition["operator"] == "=":
                condition["operator"] = "=="

            filters.append(condition)

    return ExecutionPlan(
        sheet=llm_plan.sheet,
        operation=llm_plan.operation,
        column=llm_plan.column,
        filters=filters,
        query=llm_plan.query,
    )