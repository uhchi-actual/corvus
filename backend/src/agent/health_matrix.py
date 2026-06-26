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
    health = float(focus.get("health_score") or 0)
    if health < 92.0:
        concerns.append(
            {
                "level": "watch",
                "text": f"Health score {health:.1f} sits below the strong band.",
            }
        )

    baseline_pct = float(focus.get("pct_out_of_range") or 0)
    if baseline_pct > 40.0:
        concerns.append(
            {
                "level": "watch",
                "text": f"{baseline_pct:.0f}% of samples outside the stored baseline band.",
            }
        )

    dtc_count = int(float(focus.get("dtc_count") or 0))
    if dtc_count > 0:
        concerns.append(
            {
                "level": "fault",
                "text": f"{dtc_count} fault code row(s) logged on this drive.",
            }
        )
    else:
        concerns.append(
            {
                "level": "ok",
                "text": "No fault codes in this public log.",
            }
        )

    airflow_value = float(
        next((row["value"] for row in matrix if row["id"] == "airflow"), 0)
    )
    if airflow_value < 55.0:
        concerns.append(
            {
                "level": "watch",
                "text": "Airflow swing is wide across the logged window.",
            }
        )

    if not any(item["level"] == "watch" for item in concerns):
        concerns.insert(
            0,
            {
                "level": "ok",
                "text": "No major performance flags from SQL on this drive.",
            },
        )

    return concerns[:4]


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))
