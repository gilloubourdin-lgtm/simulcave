# app/services/nrcave_results.py

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.simulcave_core.adapter import simulate_from_dict


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value in (None, ""):
            return float(default)

        return float(value)

    except (TypeError, ValueError):
        return float(default)


def _read_value(
    source: Any,
    attribute: str,
    default: Any = None,
) -> Any:
    """
    Lit une valeur depuis un objet Python ou un dictionnaire.
    """

    if isinstance(source, dict):
        return source.get(attribute, default)

    return getattr(
        source,
        attribute,
        default,
    )


def _monthly_values(
    monthly_results: list[Any] | None,
    attribute: str,
    default: float = 0.0,
) -> list[float]:
    """
    Retourne toujours un profil mensuel de douze valeurs positives.
    """

    values: list[float] = []

    for month in list(monthly_results or [])[:12]:
        raw_value = _read_value(
            month,
            attribute,
            default,
        )

        values.append(
            max(
                0.0,
                _safe_float(
                    raw_value,
                    default,
                ),
            )
        )

    while len(values) < 12:
        values.append(float(default))

    return values


def build_nrcave_result_payload(
    *,
    cave: Any,
    result: Any,
) -> dict[str, Any]:
    """
    Construit le contrat officiel SimulCave → NRCave.
    """

    monthly_results = list(
        _read_value(
            result,
            "monthly_results",
            [],
        )
        or []
    )

    monthly_heating = _monthly_values(
        monthly_results,
        "heating_kwh",
    )

    monthly_cooling = _monthly_values(
        monthly_results,
        "cooling_kwh",
    )

    monthly_temperature = _monthly_values(
        monthly_results,
        "effective_temp_c",
    )

    monthly_humidity = _monthly_values(
        monthly_results,
        "relative_humidity_percent",
        75.0,
    )

    monthly_humidity_risk = _monthly_values(
        monthly_results,
        "humidity_risk_index",
    )

    cave_length_m = _safe_float(
        getattr(cave, "length_m", 0.0)
    )
    cave_width_m = _safe_float(
        getattr(cave, "width_m", 0.0)
    )
    cave_height_m = _safe_float(
        getattr(cave, "height_m", 0.0)
    )

    surface_m2 = (
        cave_length_m
        * cave_width_m
    )

    volume_m3 = (
        surface_m2
        * cave_height_m
    )

    core_result = simulate_from_dict(
        {
            "surface_m2": surface_m2,
            "volume_m3": volume_m3,

            "annual_heating_kwh": _safe_float(
                _read_value(
                    result,
                    "total_heating_kwh",
                    0.0,
                )
            ),

            "annual_cooling_kwh": _safe_float(
                _read_value(
                    result,
                    "total_cooling_kwh",
                    0.0,
                )
            ),

            "monthly_heating_kwh": monthly_heating,
            "monthly_cooling_kwh": monthly_cooling,
            "monthly_temperature_c": monthly_temperature,
            "monthly_humidity_percent": monthly_humidity,
            "monthly_humidity_risk_index": (
                monthly_humidity_risk
            ),

            "profiles_calculated": True,

            "refrigeration_cop": _safe_float(
                _read_value(
                    result,
                    "refrigeration_cop",
                    3.0,
                ),
                3.0,
            ),

            "heat_recovery_efficiency": _safe_float(
                _read_value(
                    result,
                    "heat_recovery_efficiency",
                    0.65,
                ),
                0.65,
            ),

            "heat_recovery_temperature_c": _safe_float(
                _read_value(
                    result,
                    "heat_recovery_temperature_c",
                    35.0,
                ),
                35.0,
            ),
        }
    )

    heat_recovery = (
        core_result.get("heat_recovery")
        or {}
    )

    monthly_recoverable_heat = list(
        heat_recovery.get(
            "monthly_recoverable_heat_kwh",
            [0.0] * 12,
        )
        or [0.0] * 12
    )[:12]

    while len(monthly_recoverable_heat) < 12:
        monthly_recoverable_heat.append(0.0)

    monthly_rejected_heat = list(
        heat_recovery.get(
            "monthly_rejected_heat_kwh",
            [0.0] * 12,
        )
        or [0.0] * 12
    )[:12]

    while len(monthly_rejected_heat) < 12:
        monthly_rejected_heat.append(0.0)

    return {
        "schema_version": "1.1",
        "source": "SimulCave",
        "generated_at": datetime.now(UTC).isoformat(),

        "project": {
            "simulcave_cave_id": getattr(
                cave,
                "id",
                None,
            ),
            "name": getattr(
                cave,
                "name",
                None,
            ),
            "nrcave_cave_id": getattr(
                cave,
                "nrcave_cave_id",
                None,
            ),
            "nrcave_site_key": getattr(
                cave,
                "nrcave_site_key",
                None,
            ),
            "nrcave_instance": getattr(
                cave,
                "nrcave_instance",
                None,
            ),
        },

        "simulation_scope": core_result.get(
            "simulation_scope",
            "building_only",
        ),

        "profile_available": bool(
            core_result.get(
                "profile_available",
                False,
            )
        ),

        "thermal": {
            "monthly_heating_kwh": core_result.get(
                "monthly_heating_kwh",
                [0.0] * 12,
            ),
            "monthly_cooling_kwh": core_result.get(
                "monthly_cooling_kwh",
                [0.0] * 12,
            ),
            "monthly_ecs_kwh": core_result.get(
                "monthly_ecs_kwh",
                [0.0] * 12,
            ),
            "monthly_electricity_kwh": core_result.get(
                "monthly_electricity_kwh",
                [0.0] * 12,
            ),

            "annual_heating_kwh": core_result.get(
                "annual_heating_kwh",
                0.0,
            ),
            "annual_cooling_kwh": core_result.get(
                "annual_cooling_kwh",
                0.0,
            ),
            "annual_ecs_kwh": core_result.get(
                "annual_ecs_kwh",
                0.0,
            ),
            "annual_electricity_kwh": core_result.get(
                "annual_electricity_kwh",
                0.0,
            ),

            "recommended_hvac_power_kw": core_result.get(
                "recommended_hvac_power_kw"
            ),

            "thermal_stability_index": core_result.get(
                "thermal_stability_index"
            ),
        },

        "climate": {
            "monthly_temperature_c": core_result.get(
                "monthly_temperature_c",
                [0.0] * 12,
            ),
            "monthly_humidity_percent": core_result.get(
                "monthly_humidity_percent",
                [0.0] * 12,
            ),
            "monthly_humidity_risk_index": core_result.get(
                "monthly_humidity_risk_index",
                [0.0] * 12,
            ),
            "climate_score": _read_value(
                result,
                "climate_score",
                None,
            ),
            "climate_label": _read_value(
                result,
                "climate_label",
                None,
            ),
        },

        "indicators": {
            "energy_class": _read_value(
                result,
                "energy_class",
                None,
            ),

            "energy_intensity_kwh_m3": _read_value(
                result,
                "energy_intensity_kwh_m3",
                None,
            ),

            "annual_cost_chf": _safe_float(
                _read_value(
                    result,
                    "annual_cost_chf",
                    0.0,
                )
            ),

            "annual_co2_kg": _safe_float(
                _read_value(
                    result,
                    "annual_co2_kg",
                    0.0,
                )
            ),

            "annual_co2_tons": _safe_float(
                _read_value(
                    result,
                    "annual_co2_tons",
                    0.0,
                )
            ),
        },

        "heat_recovery": {
            "available": bool(
                heat_recovery.get(
                    "available",
                    False,
                )
            ),

            "source_type": heat_recovery.get(
                "source_type"
            ),

            "monthly_recoverable_heat_kwh": (
                monthly_recoverable_heat
            ),

            "monthly_rejected_heat_kwh": (
                monthly_rejected_heat
            ),

            "annual_recoverable_heat_kwh": (
                _safe_float(
                    heat_recovery.get(
                        "annual_recoverable_heat_kwh",
                        0.0,
                    )
                )
            ),

            "annual_rejected_heat_kwh": (
                _safe_float(
                    heat_recovery.get(
                        "annual_rejected_heat_kwh",
                        0.0,
                    )
                )
            ),

            "available_temperature_c": (
                heat_recovery.get(
                    "source_temperature_c"
                )
            ),

            "refrigeration_cop": heat_recovery.get(
                "refrigeration_cop"
            ),

            "recovery_efficiency": heat_recovery.get(
                "recovery_efficiency"
            ),

            "confidence": _safe_float(
                heat_recovery.get(
                    "confidence",
                    0.0,
                )
            ),

            "estimated": bool(
                heat_recovery.get(
                    "estimated",
                    True,
                )
            ),

            "message": heat_recovery.get(
                "message"
            ),

            "assumptions": heat_recovery.get(
                "assumptions",
                [],
            ),
        },

        "quality": core_result.get(
            "quality",
            {
                "score": 0,
                "profile_available": False,
                "assumptions": [],
                "warnings": [
                    "Qualité du calcul indisponible."
                ],
            },
        ),

        # Compatibilité temporaire avec les versions NRCave existantes.
        "thermal_needs_kwh_monthly": core_result.get(
            "monthly_heating_kwh",
            [0.0] * 12,
        ),

        "cooling_needs_kwh_monthly": core_result.get(
            "monthly_cooling_kwh",
            [0.0] * 12,
        ),

        "temperature_monthly": core_result.get(
            "monthly_temperature_c",
            [0.0] * 12,
        ),

        "humidity_monthly": core_result.get(
            "monthly_humidity_percent",
            [0.0] * 12,
        ),

        "humidity_risk_index_monthly": core_result.get(
            "monthly_humidity_risk_index",
            [0.0] * 12,
        ),

        "recommended_hvac_power_kw": core_result.get(
            "recommended_hvac_power_kw"
        ),

        "thermal_stability_index": core_result.get(
            "thermal_stability_index"
        ),

        "monthly_recoverable_heat_kwh": (
            monthly_recoverable_heat
        ),

        "annual_recoverable_heat_kwh": _safe_float(
            heat_recovery.get(
                "annual_recoverable_heat_kwh",
                0.0,
            )
        ),
    }