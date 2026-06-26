from __future__ import annotations

PIPELINE_MODULES: list[dict[str, str]] = [
    {
        "id": "ingest",
        "title": "Log the drive",
        "owner": "corvus",
        "input": "OBD-II port or CSV file",
        "output": "SQLite rows",
        "body": (
            "Raw engine readings become tidy rows: speed, RPM, air flow, "
            "temperatures, and any fault codes."
        ),
    },
    {
        "id": "sql",
        "title": "SQL math",
        "owner": "sql",
        "input": "Telemetry and baseline tables",
        "output": "Scores, trends, and evidence windows",
        "body": "Window functions and joins compute every number. No LLM touches sensor values.",
    },
    {
        "id": "huginn",
        "title": "Huginn reads now",
        "owner": "huginn",
        "input": "Current session SQL facts",
        "output": "Present-drive summary",
        "body": (
            "Lists what happened on this drive: SQL scores, sensor drift, "
            "and any logged fault codes."
        ),
    },
    {
        "id": "muninn",
        "title": "Muninn recalls normal",
        "owner": "muninn",
        "input": "Stored healthy ranges",
        "output": "Comparison and next checks",
        "body": (
            "Pulls baseline bands for this vehicle and ranks what to inspect from SQL evidence."
        ),
    },
    {
        "id": "report",
        "title": "Write the report",
        "owner": "corvus",
        "input": "Raven summaries",
        "output": "Finding plus trace id",
        "body": (
            "Stores one finding row linked to the trace id so every sentence "
            "points back to SQL rows."
        ),
    },
]

SQL_MODULE_META: dict[str, dict[str, str]] = {
    "session_health_score": {
        "title": "Drive health score",
        "query": "session_health_score.sql",
        "body": "Combines metric penalties and fault-code penalties into one 0–100 score.",
    },
    "baseline_deviation": {
        "title": "Baseline comparison",
        "query": "baseline_deviation.sql",
        "body": (
            "Counts how often each sensor sat outside the stored healthy band for this vehicle."
        ),
    },
    "fuel_trim_drift": {
        "title": "Fuel trim trend",
        "query": "fuel_trim_drift.sql",
        "body": "Rolling average of long-term fuel trim to spot lean or rich drift over time.",
    },
    "dtc_telemetry_correlation": {
        "title": "Fault code window",
        "query": "dtc_telemetry_correlation.sql",
        "body": "Pulls sensor rows from a few seconds around each logged fault code timestamp.",
    },
}


def sql_modules(analysis: dict) -> list[dict[str, str]]:
    facts = analysis.get("sql_facts", {})
    modules: list[dict[str, str]] = []

    health = facts.get("session_health_score") or {}
    if health:
        meta = SQL_MODULE_META["session_health_score"]
        modules.append(
            {
                "id": "session_health_score",
                "title": meta["title"],
                "query": meta["query"],
                "owner": "sql",
                "input": "Telemetry rows and penalty config",
                "output": (
                    f"Score {health.get('health_score', 'n/a')}; "
                    f"metric penalties {health.get('metric_penalty_points', 'n/a')}; "
                    f"fault penalties {health.get('dtc_penalty_points', 'n/a')}"
                ),
                "body": meta["body"],
            }
        )

    baseline_rows = facts.get("baseline_deviation") or []
    if baseline_rows:
        meta = SQL_MODULE_META["baseline_deviation"]
        lead = baseline_rows[0]
        modules.append(
            {
                "id": "baseline_deviation",
                "title": meta["title"],
                "query": meta["query"],
                "owner": "sql",
                "input": "Telemetry joined to baseline bands",
                "output": (
                    f"{lead.get('pct_out_of_range', 'n/a')}% outside band "
                    f"for {lead.get('metric', 'metric')} ({lead.get('context', 'context')})"
                ),
                "body": meta["body"],
            }
        )

    trim_rows = facts.get("fuel_trim_drift") or []
    if trim_rows:
        meta = SQL_MODULE_META["fuel_trim_drift"]
        last = trim_rows[-1]
        last_trim = last.get("ltft_30s", last.get("ltft_b1_pct", "n/a"))
        modules.append(
            {
                "id": "fuel_trim_drift",
                "title": meta["title"],
                "query": meta["query"],
                "owner": "sql",
                "input": "Long-term fuel trim samples",
                "output": f"Latest rolling trim {last_trim}%",
                "body": meta["body"],
            }
        )

    dtc_rows = facts.get("dtc_telemetry_correlation") or []
    meta = SQL_MODULE_META["dtc_telemetry_correlation"]
    modules.append(
        {
            "id": "dtc_telemetry_correlation",
            "title": meta["title"],
            "query": meta["query"],
            "owner": "sql",
            "input": "Fault code timestamps",
            "output": (
                f"{len(dtc_rows)} correlated sensor rows"
                if dtc_rows
                else "No fault codes to correlate"
            ),
            "body": meta["body"],
        }
    )

    return modules
