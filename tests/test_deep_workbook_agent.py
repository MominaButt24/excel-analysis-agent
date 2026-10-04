from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as app_main
from src.excel_analysis_agent.deep_workbook_agent import (
    WorkbookAnalysis,
    analyze_workbook_with_agent,
)
from executor.plan import ExecutionPlan


def test_analysis_contract_requires_evidence_fields():
    analysis = WorkbookAnalysis(
        answer="There are 2 matching rows.",
        worksheet="Inventory",
        table="Inventory",
        operation="count",
        result=2,
        source_rows=[7, 9],
    )

    assert analysis.model_dump()["source_rows"] == [7, 9]
    assert analysis.warnings == []


def test_agent_mode_requires_langsmith_key(monkeypatch):
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="LANGSMITH_API_KEY"):
        analyze_workbook_with_agent(b"workbook", "count rows")


def test_deep_agent_upload_and_query_route(monkeypatch):
    monkeypatch.setenv("EXCEL_ANALYSIS_MODE", "deep_agent")
    monkeypatch.setattr(
        app_main,
        "analyze_workbook_with_agent",
        lambda workbook, query: WorkbookAnalysis(
            answer="There are 2 matching rows.",
            worksheet="Inventory",
            table="Inventory",
            operation="count",
            result=2,
            source_rows=[7, 9],
        ),
    )

    with TestClient(app_main.app) as client:
        upload_response = client.post(
            "/upload",
            files={
                "file": (
                    "inventory.xlsx",
                    b"test-workbook-bytes",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
        )
        assert upload_response.status_code == 200
        uploaded = upload_response.json()
        assert uploaded["analysis_mode"] == "deep_agent"

        query_response = client.post(
            "/query",
            json={
                "file_id": uploaded["file_id"],
                "query": "How many matching rows are there?",
            },
        )

    assert query_response.status_code == 200
    result = query_response.json()
    assert result["result"] == 2
    assert result["evidence"]["source_rows"] == [7, 9]


def test_list_query_returns_rows_when_plan_has_no_filters(monkeypatch):
    monkeypatch.setenv("EXCEL_ANALYSIS_MODE", "deterministic")
    monkeypatch.setattr(
        app_main,
        "create_execution_plan",
        lambda query, metadata: ExecutionPlan(
            sheet="Inventory",
            operation="filter",
        ),
    )
    monkeypatch.setattr(
        app_main,
        "generate_final_response",
        lambda *args: (_ for _ in ()).throw(RuntimeError("narrator unavailable")),
    )

    workbook_bytes = Path(
        "data/uploads/inventory_parser_test.xlsx"
    ).read_bytes()
    with TestClient(app_main.app) as client:
        upload_response = client.post(
            "/upload",
            files={
                "file": (
                    "inventory_parser_test.xlsx",
                    workbook_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
        )
        file_id = upload_response.json()["file_id"]
        query_response = client.post(
            "/query",
            json={
                "file_id": file_id,
                "query": "list all electronics products",
            },
        )

    assert query_response.status_code == 200
    body = query_response.json()
    assert body["plan"]["filters"] == [{
        "column": "A",
        "operator": "==",
        "value": "Electronics",
    }]
    assert len(body["result"]) == 5
    assert body["answer"] == "Found 5 matching rows."