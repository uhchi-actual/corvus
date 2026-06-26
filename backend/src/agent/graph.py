from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from ..ingest.database import connect_sqlite
from ..sql import QueryRunner, run_session_health_score, run_session_query
from .display import enrich_trace_step
from .llm import LlmClient, LlmConfig


class AnalysisState(TypedDict):
    session_id: int
    database_path: str
    query_dir: str
    config_path: str
    disclaimer: str
    llm: LlmConfig
    agent_trace_id: str
    agent_trace: list[dict[str, str]]
    sql_facts: NotRequired[dict[str, Any]]
    dtc_events: NotRequired[list[dict[str, Any]]]
    baselines: NotRequired[list[dict[str, Any]]]
    dtc_summary: NotRequired[str]
    correlation_summary: NotRequired[str]
    recommendations: NotRequired[list[str]]
    findings: NotRequired[list[dict[str, Any]]]
    status: NotRequired[str]
    error: NotRequired[str]


def analyze_session(
    *,
    session_id: int,
    database_path: str | Path,
    query_dir: str | Path,
    config_path: str | Path,
    disclaimer: str,
    llm_config: LlmConfig,
) -> dict[str, Any]:
    trace_id = f"agent-{uuid.uuid4().hex}"
    state: AnalysisState = {
        "session_id": session_id,
        "database_path": str(database_path),
        "query_dir": str(query_dir),
        "config_path": str(config_path),
        "disclaimer": disclaimer,
        "llm": llm_config,
        "agent_trace_id": trace_id,
        "agent_trace": [
            _trace_step(
                "corvus",
                "agent_trace",
                "deterministic",
                "Trace created before analysis output.",
            )
        ],
    }

    try:
        result = _build_graph().invoke(state)
    except Exception as exc:
        state["status"] = "error"
        state["error"] = str(exc)
        state["agent_trace"] = [
            *state["agent_trace"],
            _trace_step("corvus", "error", "deterministic", "Analysis stopped with an error."),
        ]
        return _response(state)

    result["status"] = "ok"
    return _response(result)


def _build_graph() -> Any:
    graph = StateGraph(AnalysisState)
    graph.add_node("ingest_normalizer", _ingest_normalizer)
    graph.add_node("sql_deviation", _sql_deviation)
    graph.add_node("dtc_interpreter", _dtc_interpreter)
    graph.add_node("baseline_recall", _baseline_recall)
    graph.add_node("correlation", _correlation)
    graph.add_node("recommendation", _recommendation)
    graph.add_node("report_writer", _report_writer)

    graph.add_edge(START, "ingest_normalizer")
    graph.add_edge("ingest_normalizer", "sql_deviation")
    graph.add_edge("sql_deviation", "dtc_interpreter")
    graph.add_edge("dtc_interpreter", "baseline_recall")
    graph.add_edge("baseline_recall", "correlation")
    graph.add_edge("correlation", "recommendation")
    graph.add_edge("recommendation", "report_writer")
    graph.add_edge("report_writer", END)
    return graph.compile()


def _ingest_normalizer(state: AnalysisState) -> dict[str, Any]:
    with _connection(state) as conn:
        row = conn.execute(
            "SELECT session_id FROM drive_sessions WHERE session_id = ?",
            (state["session_id"],),
        ).fetchone()
    if row is None:
        raise ValueError(f"Session not found: {state['session_id']}")
    return _with_trace(
        state,
        "huginn",
        "ingest_normalizer",
        "deterministic",
        "Loaded the logged drive from the database.",
    )


def _sql_deviation(state: AnalysisState) -> dict[str, Any]:
    with _connection(state) as conn:
        facts = {
            "baseline_deviation": run_session_query(
                conn,
                state["query_dir"],
                "baseline_deviation",
                state["session_id"],
            ),
            "fuel_trim_drift": run_session_query(
                conn,
                state["query_dir"],
                "fuel_trim_drift",
                state["session_id"],
            ),
            "dtc_telemetry_correlation": run_session_query(
                conn,
                state["query_dir"],
                "dtc_telemetry_correlation",
                state["session_id"],
            ),
            "session_health_score": run_session_health_score(
                conn,
                state["query_dir"],
                state["config_path"],
                state["session_id"],
            ),
        }
    update = _with_trace(
        state,
        "huginn",
        "sql_deviation",
        "deterministic",
        "Ran SQL health score, baseline drift, trim trend, and fault-window queries.",
    )
    update["sql_facts"] = facts
    return update


def _dtc_interpreter(state: AnalysisState) -> dict[str, Any]:
    with _connection(state) as conn:
        dtc_events = QueryRunner(state["query_dir"]).run(
            conn,
            "session_dtc_events",
            {"session_id": state["session_id"]},
        )

    if dtc_events:
        summary = _llm_or_default(
            state,
            "Huginn explains logged DTC facts. Do not calculate or estimate values.",
            json.dumps({"dtc_events": dtc_events}, indent=2),
            "Logged DTC rows are available. Use their source descriptions and SQL evidence.",
        )
    else:
        summary = "No DTC rows were logged for this session."

    update = _with_trace(
        state,
        "huginn",
        "dtc_interpreter",
        "llm" if state["llm"].enabled else "deterministic",
        "Listed diagnostic trouble codes logged on this drive.",
    )
    update["dtc_events"] = dtc_events
    update["dtc_summary"] = summary
    return update


def _baseline_recall(state: AnalysisState) -> dict[str, Any]:
    with _connection(state) as conn:
        baselines = QueryRunner(state["query_dir"]).run(
            conn,
            "session_baselines",
            {"session_id": state["session_id"]},
        )
    update = _with_trace(
        state,
        "muninn",
        "baseline_recall",
        "deterministic",
        "Loaded stored healthy ranges for this vehicle.",
    )
    update["baselines"] = baselines
    return update


def _correlation(state: AnalysisState) -> dict[str, Any]:
    correlation_rows = state.get("sql_facts", {}).get("dtc_telemetry_correlation", [])
    if correlation_rows:
        summary = _llm_or_default(
            state,
            "Muninn explains SQL correlation rows. Do not calculate or estimate values.",
            json.dumps({"correlation_rows": correlation_rows}, indent=2),
            "SQL returned telemetry rows around logged DTC events.",
        )
    else:
        summary = "No DTC correlation rows were returned by SQL."
    update = _with_trace(
        state,
        "muninn",
        "correlation",
        "llm" if state["llm"].enabled else "deterministic",
        "Matched fault timestamps to nearby engine sensor rows.",
    )
    update["correlation_summary"] = summary
    return update


def _recommendation(state: AnalysisState) -> dict[str, Any]:
    prompt_payload = {
        "health_score": state.get("sql_facts", {}).get("session_health_score"),
        "baseline_deviation": state.get("sql_facts", {}).get("baseline_deviation", []),
        "dtc_events": state.get("dtc_events", []),
        "correlation": state.get("sql_facts", {}).get("dtc_telemetry_correlation", []),
    }
    text = _llm_or_default(
        state,
        "Huginn and Muninn write terse recommendations from SQL output only.",
        json.dumps(prompt_payload, indent=2),
        "Review the SQL health score, baseline rows, and DTC evidence before diagnosis.",
    )
    update = _with_trace(
        state,
        "muninn",
        "recommendation",
        "llm" if state["llm"].enabled else "deterministic",
        "Ranked what to inspect next from SQL facts only.",
    )
    update["recommendations"] = [text]
    return update


def _report_writer(state: AnalysisState) -> dict[str, Any]:
    evidence = {
        "sql_facts": state.get("sql_facts", {}),
        "dtc_summary": state.get("dtc_summary"),
        "correlation_summary": state.get("correlation_summary"),
        "recommendations": state.get("recommendations", []),
    }
    with _connection(state) as conn:
        cursor = conn.execute(
            """
            INSERT INTO findings
              (session_id, severity, category, metric_or_code, observed, expected_range,
               likely_cause, recommended_fix, confidence, evidence_json, agent_trace_id,
               created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                state["session_id"],
                "info",
                "session",
                "sql_analysis",
                json.dumps(state.get("sql_facts", {}).get("session_health_score", {})),
                "directional editable scoring config",
                state.get("dtc_summary"),
                "Inspect SQL evidence and confirm mechanically before repair.",
                None,
                json.dumps(evidence),
                state["agent_trace_id"],
            ),
        )
        conn.commit()
        finding_id = int(cursor.lastrowid)

    update = _with_trace(
        state,
        "corvus",
        "report_writer",
        "deterministic",
        "Saved the finding with trace id for audit.",
    )
    update["findings"] = [
        {
            "finding_id": finding_id,
            "session_id": state["session_id"],
            "agent_trace_id": state["agent_trace_id"],
        }
    ]
    return update


def _connection(state: AnalysisState) -> closing[sqlite3.Connection]:
    return closing(connect_sqlite(state["database_path"]))


def _llm_or_default(state: AnalysisState, system: str, user: str, default: str) -> str:
    client = LlmClient(state["llm"])
    response = client.complete(system, user)
    return response or default


def _with_trace(
    state: AnalysisState,
    agent: str,
    node: str,
    kind: str,
    summary: str,
) -> dict[str, Any]:
    return {"agent_trace": [*state["agent_trace"], _trace_step(agent, node, kind, summary)]}


def _trace_step(agent: str, node: str, kind: str, summary: str) -> dict[str, str]:
    return {
        "agent": agent,
        "node": node,
        "kind": kind,
        "summary": summary,
    }


def _response(state: AnalysisState) -> dict[str, Any]:
    return {
        "status": state.get("status", "ok"),
        "session_id": state["session_id"],
        "disclaimer": state["disclaimer"],
        "agent_trace_id": state["agent_trace_id"],
        "agent_trace": [enrich_trace_step(step) for step in state["agent_trace"]],
        "sql_facts": state.get("sql_facts", {}),
        "dtc_summary": state.get("dtc_summary"),
        "correlation_summary": state.get("correlation_summary"),
        "recommendations": state.get("recommendations", []),
        "findings": state.get("findings", []),
        "error": state.get("error"),
    }
