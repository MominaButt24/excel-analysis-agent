from fastapi import FastAPI, File, HTTPException, UploadFile

from prometheus_client import generate_latest
from fastapi.responses import Response

import os
import tempfile
import time
import uuid
from pydantic import BaseModel

from src.config.logging_config import configure_logging
from src.planner.planner import create_execution_plan
from src.planner.value_grounding import ground_categorical_filters
from src.planner.date_grounding import ground_join_date_query
from src.executor.executor import execute_plan
from src.validator.validator import validate_result
from src.llm.response import generate_final_response
from src.excel_analysis_agent.deep_workbook_agent import (
    analyze_workbook_with_agent,
)
from parser.xlsx_parser import parse_xlsx
from grounding.metadata import build_workbook_metadata

from monitoring.metrics import (
    app_health,
    xlsx_parse_total,
    xlsx_parse_failures_total,
    xlsx_parse_duration_seconds,
    query_total,
    query_failures_total,
    query_duration_seconds,
    validation_failures_total,
)

workbooks = {}
logger = configure_logging()


def get_analysis_mode():
    mode = os.getenv(
        "EXCEL_ANALYSIS_MODE",
        "deterministic",
    ).strip().lower()

    if mode not in {"deterministic", "deep_agent"}:
        raise RuntimeError(
            "EXCEL_ANALYSIS_MODE must be 'deterministic' or 'deep_agent'."
        )

    return mode


def fallback_answer(plan, result):
    if plan.operation.lower() == "count":
        return f"The count is {result}."

    if isinstance(result, list):
        return f"Found {len(result)} matching rows."

    return f"The {plan.operation} result is {result}."

app = FastAPI(
    title="Excel Analysis Agent",
    version="0.1.0",
)


class QueryRequest(BaseModel):
    file_id: str
    query: str


@app.on_event("startup")
def startup():
    app_health.set(1)
    logger.info(
        "Application started mode=%s",
        os.getenv("EXCEL_ANALYSIS_MODE", "deterministic"),
    )


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type="text/plain",
    )


@app.post("/upload")
async def upload_xlsx(
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are supported.",
        )

    file_id = str(uuid.uuid4())
    temp_path = None
    started_at = time.perf_counter()
    logger.info("Upload started file_id=%s filename=%s", file_id, file.filename)

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".xlsx",
            delete=False,
        ) as temp_file:

            temp_path = temp_file.name

            content = await file.read()
            temp_file.write(content)

        analysis_mode = get_analysis_mode()

        if analysis_mode == "deep_agent":
            parsed_workbook = None
            metadata = None
            sheet_names = []
        else:
            xlsx_parse_total.inc()

            with xlsx_parse_duration_seconds.time():
                parsed_workbook = parse_xlsx(temp_path)

            metadata = build_workbook_metadata(
                parsed_workbook
            )
            sheet_names = [
                sheet["name"]
                for sheet in parsed_workbook["sheets"]
            ]
            logger.info(
                "Workbook parsed file_id=%s sheets=%d rows=%d",
                file_id,
                len(sheet_names),
                sum(
                    len(block["rows"])
                    for sheet in parsed_workbook["sheets"]
                    for block in sheet["blocks"]
                ),
            )

        workbooks[file_id] = {
            "filename": file.filename,
            "content": content,
            "analysis_mode": analysis_mode,
            "parsed_workbook": parsed_workbook,
            "metadata": metadata,
        }

        logger.info(
            "Upload complete file_id=%s mode=%s sheets=%d bytes=%d elapsed_ms=%.1f",
            file_id,
            analysis_mode,
            len(sheet_names),
            len(content),
            (time.perf_counter() - started_at) * 1000,
        )

        return {
            "file_id": file_id,
            "filename": file.filename,
            "sheets": sheet_names,
            "metadata": metadata,
            "analysis_mode": analysis_mode,
        }

    except Exception as exc:
        xlsx_parse_failures_total.inc()
        logger.exception(
            "Upload failed file_id=%s filename=%s elapsed_ms=%.1f",
            file_id,
            file.filename,
            (time.perf_counter() - started_at) * 1000,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse XLSX: {exc}",
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/query")
def query_xlsx(request: QueryRequest):

    query_total.inc()
    started_at = time.perf_counter()
    logger.info("Query started file_id=%s", request.file_id)

    try:
        with query_duration_seconds.time():

            if request.file_id not in workbooks:
                raise HTTPException(
                    status_code=404,
                    detail="Workbook not found.",
                )

            workbook = workbooks[
                request.file_id
            ]

            if workbook["analysis_mode"] == "deep_agent":
                logger.info("Deep Agent started file_id=%s", request.file_id)
                analysis = analyze_workbook_with_agent(
                    workbook["content"],
                    request.query,
                )
                logger.info(
                    "Query complete file_id=%s mode=deep_agent operation=%s source_rows=%d elapsed_ms=%.1f",
                    request.file_id,
                    analysis.operation,
                    len(analysis.source_rows),
                    (time.perf_counter() - started_at) * 1000,
                )

                return {
                    "file_id": request.file_id,
                    "query": request.query,
                    "answer": analysis.answer,
                    "plan": {
                        "sheet": analysis.worksheet,
                        "table": analysis.table,
                        "operation": analysis.operation,
                        "filters": analysis.filters,
                    },
                    "result": analysis.result,
                    "evidence": {
                        "source_rows": analysis.source_rows,
                        "details": analysis.evidence,
                        "warnings": analysis.warnings,
                    },
                    "valid": True,
                    "analysis_mode": "deep_agent",
                }

            parsed_workbook = workbook[
                "parsed_workbook"
            ]

            metadata = workbook[
                "metadata"
            ]

            # 1. Create execution plan
            plan = create_execution_plan(
                request.query,
                metadata,
            )
            logger.info("Planner returned file_id=%s", request.file_id)
            plan = ground_categorical_filters(
                parsed_workbook,
                request.query,
                plan,
            )
            join_date_is_estimate = ground_join_date_query(
                parsed_workbook,
                request.query,
                plan,
            )
            logger.info(
                "Plan created file_id=%s sheet=%s operation=%s column=%s filters=%d",
                request.file_id,
                plan.sheet,
                plan.operation,
                plan.column,
                len(plan.filters or []),
            )

            # 2. Execute deterministically
            result = execute_plan(
                parsed_workbook,
                plan,
            )
            result_count = len(result) if isinstance(result, list) else None
            logger.info(
                "Execution complete file_id=%s operation=%s result_type=%s result_count=%s",
                request.file_id,
                plan.operation,
                type(result).__name__,
                result_count,
            )

            # 3. Validate result
            try:
                validate_result(
                    result,
                    plan,
                )
            except ValueError:
                validation_failures_total.inc()
                raise

            # 4. Generate final natural-language response
            try:
                answer = generate_final_response(
                    request.query,
                    plan,
                    result,
                )
            except Exception:
                logger.exception(
                    "Final response generation failed; returning computed result"
                )
                answer = fallback_answer(plan, result)

            warnings = []
            if join_date_is_estimate:
                answer = (
                    f"The earliest dated record is {result}. "
                    "The workbook does not identify this as a formal joining date."
                )
                warnings.append(
                    "No explicit joining-date column exists; this is the earliest dated record in the selected log, not a verified HR joining date."
                )

            logger.info(
                "Query complete file_id=%s mode=deterministic operation=%s valid=true elapsed_ms=%.1f",
                request.file_id,
                plan.operation,
                (time.perf_counter() - started_at) * 1000,
            )

            return {
                "file_id": request.file_id,
                "query": request.query,
                "answer": answer,
                "plan": {
                    "sheet": plan.sheet,
                    "operation": plan.operation,
                    "column": plan.column,
                    "filters": plan.filters,
                    "query": plan.query,
                },

                "result": result,
                "warnings": warnings,
                "valid": True,
            }

    except HTTPException:
        raise

    except ValueError as exc:
        query_failures_total.inc()
        logger.warning(
            "Query rejected file_id=%s elapsed_ms=%.1f reason=%s",
            request.file_id,
            (time.perf_counter() - started_at) * 1000,
            exc,
        )
        raise HTTPException(
            status_code=422,
            detail=f"Could not execute query: {exc}",
        )

    except Exception as exc:

        query_failures_total.inc()
        logger.exception(
            "Query failed file_id=%s elapsed_ms=%.1f",
            request.file_id,
            (time.perf_counter() - started_at) * 1000,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {exc}",
        )