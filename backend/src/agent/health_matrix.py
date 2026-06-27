from __future__ import annotations

from typing import Any


def health_matrix(
    focus: dict[str, Any],
    trend: list[dict[str, Any]],
) -> list[dict[str, str]]:
    health = float(focus.get("health_score") or 0)
    baseline_pct = float(focus.get("pct_out_of_range") or 0)
    baseline_fit = _clamp(100.0 - baseline_pct)

    dtc_count = int(float(focus.get("dtc_count") or 0))
    fault_clearance = 100.0 if dtc_count == 0 else _clamp(100.0 - dtc_count * 30.0)

    maf_values = [float(point["maf_30s"]) for point in trend if point.get("maf_30s")]
    if len(maf_values) >= 2:
        spread = max(maf_values) - min(maf_values)
        peak = max(maf_values) or 1.0
        airflow = _clamp(100.0 - (spread / peak) * 85.0)
    else:
        airflow = 50.0

    metric_penalty = float(focus.get("metric_penalty_points") or 0)
    sensor_balance = _clamp(100.0 - metric_penalty * 4.0)

    axes = [
        ("drive_health", "Drive health", health),
        ("baseline_fit", "Baseline fit", baseline_fit),
        ("airflow", "Airflow", airflow),
        ("fault_clearance", "Fault clearance", fault_clearance),
        ("sensor_balance", "Sensor balance", sensor_balance),
    ]
    return [
        {
            "id": axis_id,
            "label": label,
            "value": f"{round(value, 1):.1f}",
            "width_pct": f"{round(value, 1):.1f}%",
        }
        for axis_id, label, value in axes
    ]


def performance_concerns(
    focus: dict[str, Any],
    matrix: list[dict[str, str]],
) -> list[dict[str, str]]:
    concerns: list[dict[str, str]] = []

    baseline_pct = float(focus.get("pct_out_of_range") or 0)
    sample_count = int(float(focus.get("sample_count") or 0))
    if baseline_pct >= 50.0 and sample_count > 0:
        concerns.append(
            {
                "level": "watch",
                "text": (
                    "Coolant readings mostly sat outside the expected range "
                    "for this drive profile — check the cooling system or the "
                    "sensor before assuming normal operation."
                ),
            }
        )

    metric_penalty = float(focus.get("metric_penalty_points") or 0)
    if metric_penalty >= 8.0:
        concerns.append(
            {
                "level": "watch",
                "text": (
                    "Engine load and trim readings added measurable penalty points — "
                    "the engine may have been working harder or running less evenly "
                    "than a clean reference drive."
                ),
            }
        )

    dtc_count = int(float(focus.get("dtc_count") or 0))
    if dtc_count > 0:
        concerns.append(
            {
                "level": "fault",
                "text": (
                    f"This file logged {dtc_count} fault code row(s). "
                    "Open the fault panel for the code and the RPM, load, and "
                    "coolant rows captured around it."
                ),
            }
        )

    airflow_value = float(
        next((row["value"] for row in matrix if row["id"] == "airflow"), 0)
    )
    if airflow_value < 55.0:
        concerns.append(
            {
                "level": "watch",
                "text": (
                    "Mass airflow moved up and down sharply across the drive — "
                    "that can mean unstable idle, a boost event, or a noisy MAF signal."
                ),
            }
        )

    health = float(focus.get("health_score") or 0)
    if health < 90.0 and len(concerns) < 2:
        concerns.append(
            {
                "level": "watch",
                "text": (
                    "The SQL health score is moderate for this session — "
                    "use the airflow chart and fault panel together before "
                    "treating the drive as fully healthy."
                ),
            }
        )

    if not concerns:
        concerns.append(
            {
                "level": "ok",
                "text": (
                    "No fault codes were logged and nothing major stood out "
                    "in SQL on this public file."
                ),
            }
        )

    return concerns[:3]


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))
