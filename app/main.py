from fastapi import FastAPI, File, HTTPException, UploadFile

from prometheus_client import generate_latest
from fastapi.responses import Response

import os
import tempfile
import uuid
from pydantic import BaseModel

from src.planner.planner import create_execution_plan
from src.executor.executor import execute_plan
from src.validator.validator import validate_result
from src.llm.response import generate_final_response
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

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".xlsx",
            delete=False,
        ) as temp_file:

            temp_path = temp_file.name

            content = await file.read()
            temp_file.write(content)

        xlsx_parse_total.inc()

        with xlsx_parse_duration_seconds.time():
            parsed_workbook = parse_xlsx(temp_path)

        metadata = build_workbook_metadata(
            parsed_workbook
        )

        workbooks[file_id] = {
            "filename": file.filename,
            "parsed_workbook": parsed_workbook,
            "metadata": metadata,
        }

        return {
            "file_id": file_id,
            "filename": file.filename,
            "sheets": [
                sheet["name"]
                for sheet in parsed_workbook["sheets"]
            ],
            "metadata": metadata,
        }

    except Exception as exc:
        xlsx_parse_failures_total.inc()

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

            # 2. Execute deterministically
            result = execute_plan(
                parsed_workbook,
                plan,
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
            answer = generate_final_response(
                request.query,
                plan,
                result,
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
                "valid": True,
            }

    except HTTPException:
        raise

    except Exception as exc:

        query_failures_total.inc()

        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {exc}",
        )