from src.llm.model import (
    get_llm,
    get_langfuse_handler,
)


def generate_final_response(
    user_query: str,
    plan,
    result,
):
    llm = get_llm()
    langfuse_handler = get_langfuse_handler()

    prompt = f"""
You are the final response generator for an Excel analysis agent.

The spreadsheet operation has already been executed deterministically
by Python and the result has already been validated.

Your job is ONLY to explain the verified result clearly to the user.

Do NOT:
- recalculate the result
- invent values
- change the result
- perform spreadsheet operations
- assume information that is not present

Use the verified result exactly as provided.

USER QUERY:
{user_query}

EXECUTION PLAN:
Sheet: {plan.sheet}
Operation: {plan.operation}
Column: {plan.column}
Filters: {plan.filters}
Search query: {plan.query}

VERIFIED RESULT:
{result}

Give a concise, natural-language answer to the user's question.
"""

    response = llm.invoke(
        prompt,
        config={
            "callbacks": [langfuse_handler],
            "metadata": {
                "langfuse_tags": [
                    "excel-analysis",
                    "final-response",
                ]
            },
        },
    )

    return response.content