from datetime import datetime, UTC


def build_nrcave_payload(simulation_result: dict) -> dict:
    return {
        "source": "SimulCave",
        "version": "1.0",

        "exported_at": datetime.now(UTC).isoformat(),

        "building_model": {
        "thermal_needs_kwh_monthly": simulation_result.get(
            "thermal_needs_kwh_monthly",
            [],
        ),
        "cooling_needs_kwh_monthly": simulation_result.get(
            "cooling_needs_kwh_monthly",
            [],
        ),
        "humidity_risk_index_monthly": simulation_result.get(
            "humidity_risk_index_monthly",
            [],
        ),
        "recommended_hvac_power_kw": simulation_result.get(
            "recommended_hvac_power_kw",
            0.0,
        ),
        "temperature_monthly": simulation_result.get(
            "temperature_monthly",
            [],
        ),
        "humidity_monthly": simulation_result.get(
            "humidity_monthly",
            [],
        ),
        "thermal_stability_index": simulation_result.get(
            "thermal_stability_index",
            0.0,
        ),
        "passive_cooling_ratio": simulation_result.get(
            "passive_cooling_ratio",
            0.0,
        ),
    }
    }