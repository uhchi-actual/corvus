from __future__ import annotations

AGENT_PROFILES: dict[str, dict[str, str]] = {
    "huginn": {
        "name": "Huginn",
        "tagline": "Reads this drive",
        "role": (
            "Looks at the logged drive in front of it: sensor rows, fault codes, and SQL scores."
        ),
    },
    "muninn": {
        "name": "Muninn",
        "tagline": "Recalls what normal looks like",
        "role": "Compares this drive to stored healthy ranges and states what to inspect next.",
    },
    "corvus": {
        "name": "Corvus",
        "tagline": "Writes the report",
        "role": (
            "Stores the finding with a trace id so every conclusion links back to SQL evidence."
        ),
    },
}

NODE_LABELS: dict[str, tuple[str, str]] = {
    "agent_trace": ("Open trace", "Create an audit id before any output is written."),
    "ingest_normalizer": ("Load the drive", "Read the logged session from the database."),
    "sql_deviation": (
        "Run SQL checks",
        "Compute health score, baseline drift, fuel trim trend, and fault windows.",
    ),
    "dtc_interpreter": (
        "Read fault codes",
        "List any logged diagnostic trouble codes for this drive.",
    ),
    "baseline_recall": (
        "Load healthy ranges",
        "Pull stored baseline bands for this vehicle.",
    ),
    "correlation": (
        "Match faults to sensors",
        "Join fault timestamps to nearby engine readings.",
    ),
    "recommendation": (
        "State next checks",
        "Rank likely causes from SQL facts only.",
    ),
    "report_writer": (
        "Save finding",
        "Write the finding row and attach the trace id.",
    ),
    "error": ("Stop on error", "Analysis stopped before a finding was saved."),
}


def enrich_trace_step(step: dict[str, str]) -> dict[str, str]:
    title, default_body = NODE_LABELS.get(step["node"], (step["node"], ""))
    profile = AGENT_PROFILES.get(step["agent"], {})
    summary = step.get("summary", "")
    return {
        **step,
        "title": title,
        "body": summary or default_body,
        "agent_name": profile.get("name", step["agent"]),
        "agent_tagline": profile.get("tagline", ""),
    }
