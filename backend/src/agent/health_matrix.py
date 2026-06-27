from __future__ import annotations

from typing import Any

BALANCE_METRICS = frozenset(
    {
        "ltft_b1_pct",
        "stft_b1_pct",
        "engine_load_pct",
        "timing_adv_deg",
    }
)


def health_matrix(
    focus: dict[str, Any],
    trend: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    health = float(focus.get("health_score") or 0)
    baseline_fit = _baseline_fit_score(baseline_rows, focus)
    fault_clearance = _fault_clearance_score(focus)
    airflow = _airflow_stability_score(trend)
    sensor_balance = _sensor_balance_score(baseline_rows, focus)

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
    baseline_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    concerns: list[dict[str, str]] = []

    baseline_pct = _aggregate_pct_out_of_range(baseline_rows, focus)
    sample_count = _aggregate_sample_count(baseline_rows, focus)
    if baseline_pct >= 50.0 and sample_count > 0:
        concerns.append(
            {
                "level": "watch",
                "text": (
                    "Several logged metrics sat outside this vehicle's baseline "
                    "bands for this drive — check sensors and drive context before "
                    "assuming normal operation."
                ),
            }
        )

    coolant_pct = _metric_pct_out_of_range(baseline_rows, "coolant_temp_c")
    coolant_samples = _metric_sample_count(baseline_rows, "coolant_temp_c")
    if coolant_pct >= 50.0 and coolant_samples > 0:
        concerns.append(
            {
                "level": "watch",
                "text": (
                    "Coolant readings mostly sat outside the expected warm band — "
                    "check the cooling system or the sensor before assuming normal "
                    "operation."
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
                    "Mass airflow varied widely while the vehicle was moving — "
                    "that can mean stop-and-go traffic, unstable idle, or a noisy "
                    "MAF signal on this slice."
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


def _baseline_fit_score(
    baseline_rows: list[dict[str, Any]] | None,
    focus: dict[str, Any],
) -> float:
    scored = _scored_baseline_rows(baseline_rows)
    if scored:
        avg_out = sum(float(row.get("pct_out_of_range") or 0) for row in scored) / len(scored)
        return _clamp(100.0 - avg_out)

    baseline_pct = float(focus.get("pct_out_of_range") or 0)
    return _clamp(100.0 - baseline_pct)


def _sensor_balance_score(
    baseline_rows: list[dict[str, Any]] | None,
    focus: dict[str, Any],
) -> float:
    balance_rows = [
        row
        for row in _scored_baseline_rows(baseline_rows)
        if row.get("metric") in BALANCE_METRICS
    ]
    if balance_rows:
        avg_out = sum(float(row.get("pct_out_of_range") or 0) for row in balance_rows) / len(
            balance_rows
        )
        return _clamp(100.0 - avg_out)

    metric_penalty = float(focus.get("metric_penalty_points") or 0)
    return _clamp(100.0 - metric_penalty * 4.0)


def _fault_clearance_score(focus: dict[str, Any]) -> float:
    dtc_count = int(float(focus.get("dtc_count") or 0))
    return 100.0 if dtc_count == 0 else _clamp(100.0 - dtc_count * 30.0)


def _airflow_stability_score(trend: list[dict[str, Any]]) -> float:
    values: list[float] = []
    for point in trend:
        maf = float(point.get("maf_30s") or 0)
        if maf <= 0:
            continue
        speed_raw = point.get("speed_kph")
        if speed_raw is not None and str(speed_raw).strip() != "":
            speed = float(speed_raw)
            if speed <= 0:
                continue
        values.append(maf)

    if len(values) < 2:
        return 50.0

    mean = sum(values) / len(values)
    if mean <= 0:
        return 50.0

    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = variance ** 0.5
    coefficient_of_variation = std / mean
    return _clamp(100.0 - min(85.0, coefficient_of_variation * 100.0))


def _scored_baseline_rows(baseline_rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not baseline_rows:
        return []
    scored: list[dict[str, Any]] = []
    for row in baseline_rows:
        sample_count = int(float(row.get("sample_count") or 0))
        pct = row.get("pct_out_of_range")
        if sample_count <= 0 or pct is None:
            continue
        scored.append(row)
    return scored


def _aggregate_pct_out_of_range(
    baseline_rows: list[dict[str, Any]] | None,
    focus: dict[str, Any],
) -> float:
    scored = _scored_baseline_rows(baseline_rows)
    if scored:
        return sum(float(row.get("pct_out_of_range") or 0) for row in scored) / len(scored)
    return float(focus.get("pct_out_of_range") or 0)


def _aggregate_sample_count(
    baseline_rows: list[dict[str, Any]] | None,
    focus: dict[str, Any],
) -> int:
    scored = _scored_baseline_rows(baseline_rows)
    if scored:
        return sum(int(float(row.get("sample_count") or 0)) for row in scored)
    return int(float(focus.get("sample_count") or 0))


def _metric_pct_out_of_range(
    baseline_rows: list[dict[str, Any]] | None,
    metric: str,
) -> float:
    if not baseline_rows:
        return 0.0
    for row in baseline_rows:
        if row.get("metric") == metric:
            return float(row.get("pct_out_of_range") or 0)
    return 0.0


def _metric_sample_count(baseline_rows: list[dict[str, Any]] | None, metric: str) -> int:
    if not baseline_rows:
        return 0
    for row in baseline_rows:
        if row.get("metric") == metric:
            return int(float(row.get("sample_count") or 0))
    return 0


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))
