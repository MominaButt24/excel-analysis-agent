from pathlib import Path
from typing import Any
from datetime import timedelta

import json
import os
import shlex
import time
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import generate_latest

from opensandbox import SandboxSync
from opensandbox.config.connection_sync import ConnectionConfigSync
from opensandbox.models.filesystem import WriteEntry

from src.config.logging_config import configure_logging

from src.excel_analysis_agent.deep_workbook_agent import (
    analyze_workbook_with_agent,
)

from monitoring.metrics import (
    app_health,
    xlsx_parse_total,
    xlsx_parse_failures_total,
    xlsx_parse_duration_seconds,
    query_total,
    query_failures_total,
    query_duration_seconds,
)


# -------------------------------------------------------------------
# Application state
# -------------------------------------------------------------------

workbooks: dict[str, dict[str, Any]] = {}

logger = configure_logging()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SANDBOX_IMAGE = "python:3.12"

ANALYSIS_MODE = os.getenv(
    "EXCEL_ANALYSIS_MODE",
    "deep_agent",
).lower()


app = FastAPI(
    title="Excel Analysis Agent",
    version="0.1.0",
)


class QueryRequest(BaseModel):
    file_id: str
    query: str


# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------

def log_phase(message: str, *args):
    logger.info("[PHASE] " + message, *args)


# -------------------------------------------------------------------
# OpenSandbox helpers
# -------------------------------------------------------------------

def create_sandbox() -> SandboxSync:
    log_phase("Creating OpenSandbox")

    config = ConnectionConfigSync(
        domain=os.getenv(
            "OPEN_SANDBOX_DOMAIN",
            "localhost:8080",
        ),
        api_key=os.getenv(
            "OPEN_SANDBOX_API_KEY",
        ),
        use_server_proxy=True,
    )

    sandbox = SandboxSync.create(
        SANDBOX_IMAGE,
        connection_config=config,
        timeout=timedelta(hours=1),
    )

    log_phase("OpenSandbox created")

    return sandbox


def build_sandbox_files(
    workbook_bytes: bytes,
) -> list[WriteEntry]:

    entries: list[WriteEntry] = []

    # ---------------------------------------------------------------
    # 1. Workbook
    # ---------------------------------------------------------------

    entries.append(
        WriteEntry(
            path="/workspace/workbook.xlsx",
            data=workbook_bytes,
            mode=644,
        )
    )

    # ---------------------------------------------------------------
    # 2. Existing deterministic Excel source
    #
    # Local:
    #   src/parser/
    #   src/grounding/
    #   src/executor/
    #
    # Remote:
    #   /workspace/excel_agent_src/parser/
    #   /workspace/excel_agent_src/grounding/
    #   /workspace/excel_agent_src/executor/
    # ---------------------------------------------------------------

    source_root = PROJECT_ROOT / "src"

    source_directories = [
        "parser",
        "grounding",
        "executor",
    ]

    for directory_name in source_directories:

        local_directory = (
            source_root / directory_name
        )

        if not local_directory.exists():
            raise FileNotFoundError(
                f"Required source directory not found: "
                f"{local_directory}"
            )

        for local_file in local_directory.rglob("*"):

            if not local_file.is_file():
                continue

            relative_path = (
                local_file
                .relative_to(source_root)
                .as_posix()
            )

            remote_path = (
                "/workspace/excel_agent_src/"
                + relative_path
            )

            entries.append(
                WriteEntry(
                    path=remote_path,
                    data=local_file.read_bytes(),
                    mode=644,
                )
            )

    # ---------------------------------------------------------------
    # 3. Excel analysis skill
    # ---------------------------------------------------------------

    skill_path = (
        PROJECT_ROOT
        / "skills"
        / "excel-workbook-analysis"
        / "SKILL.md"
    )

    if not skill_path.exists():
        raise FileNotFoundError(
            f"Skill file not found: {skill_path}"
        )

    entries.append(
        WriteEntry(
            path=(
                "/workspace/skills/"
                "excel-workbook-analysis/SKILL.md"
            ),
            data=skill_path.read_bytes(),
            mode=644,
        )
    )

    # ---------------------------------------------------------------
    # 4. Sandbox runner
    # ---------------------------------------------------------------

    runner_path = (
        PROJECT_ROOT
        / "src"
        / "excel_analysis_agent"
        / "sandbox_runner.py"
    )

    if not runner_path.exists():
        raise FileNotFoundError(
            f"Sandbox runner not found: {runner_path}"
        )

    entries.append(
        WriteEntry(
            path="/workspace/workbook_runner.py",
            data=runner_path.read_bytes(),
            mode=644,
        )
    )

    return entries


def run_sandbox_function(
    sandbox: SandboxSync,
    function_name: str,
    **kwargs,
):
    """
    Call one function exposed by workbook_runner.py.

    stdout:
        JSON result only.

    stderr:
        sandbox phase logs.
    """

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

    result = sandbox.commands.run(command)

    stdout = "".join(
        output.text
        for output in result.logs.stdout
    )

    stderr = "".join(
        output.text
        for output in result.logs.stderr
    )

    # ---------------------------------------------------------------
    # Sandbox runner logs belong to stderr.
    # They are NOT automatically failures.
    # ---------------------------------------------------------------

    if stderr:
        for line in stderr.splitlines():
            if line.strip():
                logger.info(
                    "[SANDBOX] %s",
                    line,
                )

    if not stdout.strip():
        raise RuntimeError(
            f"Sandbox function '{function_name}' "
            "returned no JSON output."
        )

    try:
        return json.loads(stdout)

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            f"Invalid JSON from sandbox function "
            f"'{function_name}': {stdout[:2000]}"
        ) from exc


def prepare_sandbox(
    workbook_bytes: bytes,
):
    """
    Create and prepare the sandbox for workbook analysis.

    The sandbox is prepared once during upload and kept alive
    for subsequent /query requests.
    """

    sandbox = None
    parse_attempted = False

    try:

        # -----------------------------------------------------------
        # 1. Create sandbox
        # -----------------------------------------------------------

        sandbox = create_sandbox()

        # -----------------------------------------------------------
        # 2. Install required sandbox dependencies
        #
        # The sandbox uses a clean python:3.12 image, so packages
        # installed on the host machine are not available inside it.
        # -----------------------------------------------------------

        # log_phase(
        #     "Installing sandbox dependency: openpyxl"
        # )

        # install_result = sandbox.commands.run(
        #     "python -m pip install -q openpyxl"
        # )

        # install_stdout = "".join(
        #     output.text
        #     for output in install_result.logs.stdout
        # )

        # install_stderr = "".join(
        #     output.text
        #     for output in install_result.logs.stderr
        # )

        # if install_stdout:
        #     logger.info(
        #         "[SANDBOX INSTALL] %s",
        #         install_stdout.strip(),
        #     )

        # if install_stderr:
        #     logger.info(
        #         "[SANDBOX INSTALL] %s",
        #         install_stderr.strip(),
        #     )

        # log_phase(
        #     "Sandbox dependency ready: openpyxl"
        # )

        # -----------------------------------------------------------
        # 2. Install and VERIFY sandbox dependencies
        # -----------------------------------------------------------

        log_phase(
            "Installing sandbox dependency: openpyxl"
        )

        install_result = sandbox.commands.run(
            "python -m pip install -q "
            "--root-user-action=ignore "
            "--disable-pip-version-check "
            "openpyxl "
            "&& "
            "python -c "
            "'import openpyxl; print(openpyxl.__version__)'"
        )

        install_stdout = "".join(
            output.text
            for output in install_result.logs.stdout
        )

        install_stderr = "".join(
            output.text
            for output in install_result.logs.stderr
        )

        # -----------------------------------------------------------
        # Check actual command failure
        # -----------------------------------------------------------

        if getattr(install_result, "error", None):

            raise RuntimeError(
                "Failed to install/verify openpyxl: "
                f"{install_result.error}"
            )

        if (
            getattr(install_result, "exit_code", None)
            not in (None, 0)
        ):

            raise RuntimeError(
                "Failed to install/verify openpyxl "
                f"(exit_code={install_result.exit_code}). "
                f"stdout={install_stdout[:1000]} "
                f"stderr={install_stderr[:1000]}"
            )

        # -----------------------------------------------------------
        # Log the verified version
        # -----------------------------------------------------------

        logger.info(
            "[SANDBOX INSTALL] openpyxl verified version=%s",
            install_stdout.strip(),
        )

        log_phase(
            "Sandbox dependency ready: openpyxl"
        )
        # -----------------------------------------------------------
        # 3. Upload workbook + parser + grounding + executor
        #    + skill + runner
        # -----------------------------------------------------------

        log_phase(
            "Preparing sandbox files"
        )

        entries = build_sandbox_files(
            workbook_bytes
        )

        sandbox.files.write_files(
            entries
        )

        log_phase(
            "Sandbox files uploaded count=%d",
            len(entries),
        )

        # -----------------------------------------------------------
        # 4. Initial structural inspection
        #
        # Deterministic parser only.
        # No LLM involved here.
        # -----------------------------------------------------------

        log_phase(
            "Running initial workbook inspection"
        )

        parse_attempted = True
        xlsx_parse_total.inc()

        with xlsx_parse_duration_seconds.time():

            structure = run_sandbox_function(
                sandbox,
                "inspect_workbook",
            )

        sheet_names = [
            sheet["name"]
            for sheet in structure.get(
                "sheets",
                [],
            )
        ]

        log_phase(
            "Workbook inspection complete sheets=%d",
            len(sheet_names),
        )

        return sandbox, structure

    except Exception:

        if parse_attempted:
            xlsx_parse_failures_total.inc()

        if sandbox is not None:

            try:

                sandbox.destroy()

                log_phase(
                    "Sandbox destroyed after preparation failure"
                )

            except Exception:

                logger.exception(
                    "Failed to destroy sandbox "
                    "after preparation failure"
                )

        raise


# -------------------------------------------------------------------
# Startup / shutdown
# -------------------------------------------------------------------

@app.on_event("startup")
def startup():

    app_health.set(1)

    logger.info(
        "Application started mode=%s",
        ANALYSIS_MODE,
    )


@app.on_event("shutdown")
def shutdown():

    logger.info(
        "Application shutting down; "
        "destroying active sandboxes count=%d",
        len(workbooks),
    )

    for file_id, workbook in list(
        workbooks.items()
    ):

        sandbox = workbook.get("sandbox")

        if sandbox is None:
            continue

        try:

            sandbox.destroy()

            logger.info(
                "[SANDBOX DESTROYED] file_id=%s",
                file_id,
            )

        except Exception:

            logger.exception(
                "Failed to destroy sandbox "
                "file_id=%s",
                file_id,
            )

    workbooks.clear()


# -------------------------------------------------------------------
# Health
# -------------------------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "active_workbooks": len(workbooks),
        "analysis_mode": ANALYSIS_MODE,
    }


# -------------------------------------------------------------------
# Metrics
# -------------------------------------------------------------------

@app.get("/metrics")
def metrics():

    return Response(
        generate_latest(),
        media_type="text/plain",
    )


# -------------------------------------------------------------------
# Upload
# -------------------------------------------------------------------

@app.post("/upload")
async def upload_xlsx(
    file: UploadFile = File(...),
):

    filename = file.filename or ""

    if not filename.lower().endswith(".xlsx"):

        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are supported.",
        )

    file_id = str(uuid.uuid4())

    started_at = time.perf_counter()

    logger.info(
        "[UPLOAD START] file_id=%s filename=%s",
        file_id,
        filename,
    )

    try:

        # -----------------------------------------------------------
        # Read upload
        # -----------------------------------------------------------

        log_phase(
            "Reading uploaded workbook file_id=%s",
            file_id,
        )

        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded workbook is empty.",
            )

        logger.info(
            "[UPLOAD] file_id=%s bytes=%d",
            file_id,
            len(content),
        )

        # -----------------------------------------------------------
        # Current architecture
        # -----------------------------------------------------------

        if ANALYSIS_MODE != "deep_agent":

            raise HTTPException(
                status_code=500,
                detail=(
                    "Only deep_agent mode is supported "
                    "in the current architecture."
                ),
            )

        # -----------------------------------------------------------
        # Create + prepare sandbox
        # -----------------------------------------------------------

        sandbox, structure = prepare_sandbox(
            content,
        )

        sheet_names = [
            sheet["name"]
            for sheet in structure.get(
                "sheets",
                [],
            )
        ]

        # -----------------------------------------------------------
        # Keep sandbox alive for future /query calls
        # -----------------------------------------------------------

        workbooks[file_id] = {
            "filename": filename,
            "analysis_mode": "deep_agent",
            "sandbox": sandbox,
            "workbook_structure": structure,
        }

        logger.info(
            "[UPLOAD COMPLETE] "
            "file_id=%s mode=deep_agent sheets=%d "
            "bytes=%d elapsed_ms=%.1f",
            file_id,
            len(sheet_names),
            len(content),
            (
                time.perf_counter()
                - started_at
            ) * 1000,
        )

        return {
            "file_id": file_id,
            "filename": filename,
            "sheets": sheet_names,
            "workbook_structure": structure,
            "analysis_mode": "deep_agent",
        }

    except HTTPException:
        raise

    except Exception as exc:

        logger.exception(
            "[UPLOAD FAILED] "
            "file_id=%s filename=%s elapsed_ms=%.1f",
            file_id,
            filename,
            (
                time.perf_counter()
                - started_at
            ) * 1000,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare XLSX: {exc}",
        )


# -------------------------------------------------------------------
# Query
# -------------------------------------------------------------------

@app.post("/query")
async def query_xlsx(
    request: QueryRequest,
):

    query_total.inc()

    started_at = time.perf_counter()

    logger.info(
        "[QUERY START] file_id=%s query=%s",
        request.file_id,
        request.query,
    )

    try:

        with query_duration_seconds.time():

            # -------------------------------------------------------
            # Find existing workbook session
            # -------------------------------------------------------

            workbook = workbooks.get(
                request.file_id
            )

            if workbook is None:

                raise HTTPException(
                    status_code=404,
                    detail="Workbook not found.",
                )

            sandbox = workbook.get(
                "sandbox"
            )

            if sandbox is None:

                raise HTTPException(
                    status_code=500,
                    detail="Workbook sandbox is unavailable.",
                )

            logger.info(
                "[QUERY] Reusing sandbox file_id=%s",
                request.file_id,
            )

            # -------------------------------------------------------
            # Deep Agent
            #
            # IMPORTANT:
            # analyze_workbook_with_agent must now accept
            # the already-created sandbox.
            # -------------------------------------------------------

            logger.info(
                "[AGENT START] file_id=%s",
                request.file_id,
            )

            analysis = (
                await analyze_workbook_with_agent(
                    sandbox=sandbox,
                    query=request.query,
                )
            )

            logger.info(
                "[AGENT COMPLETE] file_id=%s "
                "operation=%s",
                request.file_id,
                analysis.operation,
            )

            # -------------------------------------------------------
            # Response
            # -------------------------------------------------------

            logger.info(
                "[QUERY COMPLETE] "
                "file_id=%s elapsed_ms=%.1f",
                request.file_id,
                (
                    time.perf_counter()
                    - started_at
                ) * 1000,
            )

            return {
                "file_id": request.file_id,
                "query": request.query,

                "answer": analysis.answer,

                "plan": {
                    "sheet": analysis.worksheet,
                    "table": analysis.table,
                    "operation": analysis.operation,
                    "column": getattr(
                        analysis,
                        "column",
                        None,
                    ),
                    "filters": analysis.filters,
                },

                "result": analysis.result,

                "evidence": {
                    "source_rows": analysis.source_rows,
                    "details": analysis.evidence,
                    "warnings": analysis.warnings,
                },

                "valid": True,

                "pipeline": "deep_agent",
            }

    except HTTPException:
        raise

    except Exception as exc:

        query_failures_total.inc()

        logger.exception(
            "[QUERY FAILED] file_id=%s "
            "elapsed_ms=%.1f",
            request.file_id,
            (
                time.perf_counter()
                - started_at
            ) * 1000,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {exc}",
        )