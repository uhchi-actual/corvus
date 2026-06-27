from __future__ import annotations

from src.agent.health_matrix import health_matrix


def test_health_matrix_uses_per_session_baselines_not_cross_vehicle_averages() -> None:
    focus = {
        "health_score": "96.0",
        "metric_penalty_points": "4.0",
        "dtc_count": "0",
        "pct_out_of_range": "0.0",
        "sample_count": "0",
    }
    trend = [
        {"maf_30s": "10.0", "speed_kph": "25.0"},
        {"maf_30s": "12.0", "speed_kph": "30.0"},
        {"maf_30s": "11.0", "speed_kph": "28.0"},
        {"maf_30s": "0.0", "speed_kph": "0.0"},
    ]
    baseline_rows = [
        {
            "metric": "engine_load_pct",
            "context": "session",
            "sample_count": 100,
            "out_of_range_samples": 5,
            "pct_out_of_range": 5.0,
        }
    ]

    matrix = health_matrix(focus, trend, baseline_rows)
    by_id = {row["id"]: float(row["value"]) for row in matrix}

    assert by_id["drive_health"] == 96.0
    assert by_id["baseline_fit"] == 95.0
    assert by_id["sensor_balance"] == 95.0
    assert by_id["fault_clearance"] == 100.0
    assert by_id["airflow"] > 70.0


def test_airflow_ignores_stopped_samples_with_zero_speed() -> None:
    focus = {"health_score": "100.0", "metric_penalty_points": "0.0", "dtc_count": "0"}
    stable = [{"maf_30s": "10.0", "speed_kph": "20.0"}, {"maf_30s": "10.5", "speed_kph": "22.0"}]
    volatile = [
        {"maf_30s": "20.0", "speed_kph": "40.0"},
        {"maf_30s": "2.0", "speed_kph": "40.0"},
        {"maf_30s": "0.0", "speed_kph": "0.0"},
    ]

    stable_score = float(
        next(row["value"] for row in health_matrix(focus, stable, []) if row["id"] == "airflow")
    )
    volatile_score = float(
        next(row["value"] for row in health_matrix(focus, volatile, []) if row["id"] == "airflow")
    )

    assert stable_score > volatile_score
