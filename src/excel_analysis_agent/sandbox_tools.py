import json
import logging
import shlex
import time
from typing import Literal

from langchain_core.tools import tool
from opensandbox.models import WriteEntry


logger = logging.getLogger(
    "excel_analysis_agent.deep_agent.tools"
)


# -------------------------------------------------------------------
# Run a function inside the existing sandbox
# -------------------------------------------------------------------

def run_sandbox_function(
    sandbox,
    function_name: str,
    **kwargs,
):
    started_at = time.perf_counter()

    logger.info(
        "[TOOL START] %s args=%s",
        function_name,
        kwargs,
    )

    payload = json.dumps(kwargs)

    command = (
        "python -c "
        + shlex.quote(
            f"""
import sys
import json

sys.path.insert(0, "/workspace")

from workbook_runner import {function_name}

args = json.loads({payload!r})

result = {function_name}(**args)

print(json.dumps(result, default=str))
"""
        )
    )

    try:

        result = sandbox.commands.run(
            command
        )

        stdout = "".join(
            output.text
            for output in result.logs.stdout
        )

        stderr = "".join(
            output.text
            for output in result.logs.stderr
        )

        # -----------------------------------------------------------
        # stderr is used by sandbox_runner for normal logging.
        # Forward those logs to the main terminal logger.
        # Do NOT treat stderr itself as a failure.
        # -----------------------------------------------------------

        if stderr:

            for line in stderr.splitlines():

                if line.strip():

                    logger.info(
                        "[SANDBOX] %s",
                        line,
                    )

        # -----------------------------------------------------------
        # stdout must contain the JSON result.
        # -----------------------------------------------------------

        if not stdout.strip():

            raise RuntimeError(
                f"Sandbox function '{function_name}' "
                "returned no stdout."
            )

        try:

            output = json.loads(
                stdout
            )

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                f"Sandbox function '{function_name}' "
                f"returned invalid JSON: "
                f"{stdout[:2000]}"
            ) from exc

        logger.info(
            "[TOOL END] %s elapsed_ms=%.1f",
            function_name,
            (
                time.perf_counter()
                - started_at
            ) * 1000,
        )

        return output

    except Exception:

        logger.exception(
            "[TOOL FAILED] %s",
            function_name,
        )

        raise


# -------------------------------------------------------------------
# Create Excel tools bound to one sandbox
# -------------------------------------------------------------------

def create_excel_tools(sandbox):

    # ---------------------------------------------------------------
    # Inspect workbook
    # ---------------------------------------------------------------

    @tool
    def inspect_workbook_tool():
        """
        Inspect workbook structure.

        Returns sheets, dimensions, headers, columns,
        and structural blocks.

        Use before making structural assumptions.
        """

        return run_sandbox_function(
            sandbox,
            "inspect_workbook",
        )

    # ---------------------------------------------------------------
    # Inspect one sheet
    # ---------------------------------------------------------------

    @tool
    def inspect_sheet_tool(
        sheet_name: str,
    ):
        """
        Inspect the structure of one worksheet.

        Use when detailed structure for a specific sheet
        is required.
        """

        return run_sandbox_function(
            sandbox,
            "inspect_sheet",
            sheet_name=sheet_name,
        )

    # ---------------------------------------------------------------
    # Deterministic Excel query
    # ---------------------------------------------------------------

    @tool
    def excel_query_tool(
        sheet: str,
        operation: Literal[
            "count",
            "sum",
            "average",
            "minimum",
            "maximum",
            "search",
            "filter",
            "sort",
        ],
        column: str | None = None,
        filters: list[dict] | None = None,
        query: str | None = None,
    ):
        """
        Execute an operation using the deterministic Excel engine.

        Prefer this tool whenever the requested operation is directly
        supported.

        Supported:
        - count
        - sum
        - average
        - minimum
        - maximum
        - search
        - filter
        - sort

        Do NOT recreate these operations with custom Python.

        Use sandbox_execute_python only for:
        - custom analysis
        - derived calculations
        - multi-step calculations
        - hypothetical questions
        - sequence-based analysis
        - unsupported operations
        """

        return run_sandbox_function(
            sandbox,
            "excel_query",
            sheet=sheet,
            operation=operation,
            column=column,
            filters=filters,
            query=query,
        )

    # ---------------------------------------------------------------
    # Raw workbook text search
    # ---------------------------------------------------------------

    @tool
    def search_workbook_text_tool(
        query: str,
        sheet_name: str | None = None,
    ):
        """
        Search actual workbook cells for raw text.

        Useful for:
        - leave markers
        - notes
        - section headers
        - names
        - labels
        - merged-cell content
        - other structural/unclassified text

        This discovers evidence.

        It does not perform calculations.
        """

        return run_sandbox_function(
            sandbox,
            "search_workbook_text",
            query=query,
            sheet_name=sheet_name,
        )

    # ---------------------------------------------------------------
    # Custom Python execution
    # ---------------------------------------------------------------

    @tool
    def sandbox_execute_python(
        python_code: str,
    ):
        """
        Execute custom Python inside the isolated Excel sandbox.

        Use ONLY when deterministic tools are insufficient or when
        the question requires custom, derived, multi-step,
        hypothetical, sequence-based, or unsupported analysis.

        Workbook:
            /workspace/workbook.xlsx

        For generic workbook analysis:

        - inspect workbook structure first
        - prefer /workspace/excel_agent_src parser logic
        - use openpyxl when structural content matters
        - identify actual detail/data rows
        - never infer business meaning from row counts
        - never assume Date/Day means a real record
        - return compact results with evidence coordinates
        - never dump the workbook
        """

        started_at = time.perf_counter()

        logger.info(
            "[PYTHON START] generated sandbox analysis"
        )

        logger.info(
            "[PYTHON CODE START]"
        )

        for line in python_code.splitlines():
            logger.info(
                "[PYTHON CODE] %s",
                line,
            )

        logger.info(
            "[PYTHON CODE END]"
        )

        script_path = (
            "/workspace/generated_analysis.py"
        )

        # -----------------------------------------------------------
        # Upload generated script
        # -----------------------------------------------------------

        sandbox.files.write_files([
            WriteEntry(
                path=script_path,
                data=python_code.encode(),
            )
        ])

        logger.info(
            "[PYTHON] Script uploaded: %s",
            script_path,
        )

        try:

            # -------------------------------------------------------
            # Execute directly.
            #
            # Do NOT use `2>&1 | head` here.
            # That can hide the real process failure status.
            # We bound the returned output in Python below instead.
            # -------------------------------------------------------

            logger.info(
                "[PYTHON] Executing generated script"
            )

            result = sandbox.commands.run(
                f"python {script_path}"
            )

            stdout = "".join(
                output.text
                for output in result.logs.stdout
            )

            stderr = "".join(
                output.text
                for output in result.logs.stderr
            )

            # -------------------------------------------------------
            # Forward script logs to terminal.
            # -------------------------------------------------------

            if stderr:

                for line in stderr.splitlines():

                    if line.strip():

                        logger.info(
                            "[PYTHON STDERR] %s",
                            line,
                        )

            output = stdout

            if not output and stderr:
                output = stderr

            # -------------------------------------------------------
            # Bound tool output
            # -------------------------------------------------------

            MAX_OUTPUT = 12000

            truncated = (
                len(output)
                > MAX_OUTPUT
            )

            bounded_output = output[
                :MAX_OUTPUT
            ]

            logger.info(
                "[PYTHON END] elapsed_ms=%.1f "
                "output_chars=%d truncated=%s",
                (
                    time.perf_counter()
                    - started_at
                ) * 1000,
                len(output),
                truncated,
            )

            return {
                "script": python_code,
                "output": bounded_output,
                "truncated": truncated,
            }

        except Exception:

            logger.exception(
                "[PYTHON FAILED]"
            )

            raise

    # ---------------------------------------------------------------
    # Tool collection
    # ---------------------------------------------------------------

    tools = [
        inspect_workbook_tool,
        inspect_sheet_tool,
        excel_query_tool,
        search_workbook_text_tool,
        sandbox_execute_python,
    ]

    logger.info(
        "[TOOLS READY] %s",
        ", ".join(
            tool.name
            for tool in tools
        ),
    )

    return tools