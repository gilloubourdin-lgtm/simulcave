# app/simulcave_core/engine.py

from __future__ import annotations

from typing import Any
from app.simulcave_core.heat_recovery import (
    estimate_recoverable_heat,
)


MONTH_COUNT = 12


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


def _safe_monthly(
    value: Any,
) -> list[float]:
    """
    Retourne toujours une liste de douze valeurs positives.
    """

    if not isinstance(value, (list, tuple)):
        return [0.0] * MONTH_COUNT

    values = [
        max(0.0, _safe_float(item))
        for item in list(value)[:MONTH_COUNT]
    ]

    if len(values) < MONTH_COUNT:
        values.extend(
            [0.0] * (MONTH_COUNT - len(values))
        )

    return values


def _monthly_from_annual(
    annual_value: float,
    shape: list[float] | None = None,
) -> list[float]:
    annual_value = max(
        0.0,
        _safe_float(annual_value),
    )

    if annual_value <= 0:
        return [0.0] * MONTH_COUNT

    if not shape or len(shape) != MONTH_COUNT:
        return [
            round(annual_value / MONTH_COUNT, 3)
            for _ in range(MONTH_COUNT)
        ]

    positive_shape = [
        max(0.0, _safe_float(value))
        for value in shape
    ]

    shape_sum = sum(positive_shape)

    if shape_sum <= 0:
        return [
            round(annual_value / MONTH_COUNT, 3)
            for _ in range(MONTH_COUNT)
        ]

    return [
        round(
            annual_value * value / shape_sum,
            3,
        )
        for value in positive_shape
    ]


def _recommended_power_kw(
    monthly_heating_kwh: list[float],
    monthly_cooling_kwh: list[float],
) -> float:
    """
    Estimation indicative à partir du mois le plus chargé.

    Elle ne remplace pas un calcul horaire de puissance.
    """

    monthly_peak = max(
        monthly_heating_kwh
        + monthly_cooling_kwh
        + [0.0]
    )

    # Environ 300 heures équivalentes pendant le mois critique.
    return round(
        monthly_peak / 300.0,
        1,
    )


def _thermal_stability_index(
    monthly_temperature_c: list[float],
) -> float | None:
    available = [
        value
        for value in monthly_temperature_c
        if value is not None
    ]

    if not available:
        return None

    amplitude = max(available) - min(available)

    return round(
        max(
            0.0,
            min(
                100.0,
                100.0 - amplitude * 6.0,
            ),
        ),
        1,
    )


def run_simulation(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Point d'entrée public du moteur SimulCave.

    Aucun FastAPI, HTML ou accès SQLAlchemy ne doit être ajouté ici.

    Le moteur donne la priorité aux profils mensuels calculés.
    Les estimations annuelles simplifiées ne sont utilisées qu'en fallback.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Le moteur SimulCave attend un dictionnaire."
        )

    surface_m2 = max(
        0.0,
        _safe_float(data.get("surface_m2")),
    )

    volume_m3 = max(
        0.0,
        _safe_float(data.get("volume_m3")),
    )

    production_hl = max(
        0.0,
        _safe_float(data.get("production_hl")),
    )

    annual_electricity_kwh = max(
        0.0,
        _safe_float(
            data.get("annual_electricity_kwh")
            or data.get("total_electricity_kwh")
        ),
    )

    annual_heating_input = max(
        0.0,
        _safe_float(
            data.get("annual_heating_kwh")
            or data.get("heating_kwh")
        ),
    )

    annual_cooling_input = max(
        0.0,
        _safe_float(
            data.get("annual_cooling_kwh")
            or data.get("cooling_kwh")
        ),
    )

    annual_ecs_input = max(
        0.0,
        _safe_float(
            data.get("annual_ecs_kwh")
            or data.get("ecs_kwh")
        ),
    )

    monthly_heating = _safe_monthly(
        data.get("monthly_heating_kwh")
    )

    monthly_cooling = _safe_monthly(
        data.get("monthly_cooling_kwh")
    )

    monthly_ecs = _safe_monthly(
        data.get("monthly_ecs_kwh")
    )

    monthly_electricity = _safe_monthly(
        data.get("monthly_electricity_kwh")
    )

    monthly_temperature = _safe_monthly(
        data.get("monthly_temperature_c")
    )

    monthly_humidity = _safe_monthly(
        data.get("monthly_humidity_percent")
    )

    monthly_humidity_risk = _safe_monthly(
        data.get("monthly_humidity_risk_index")
    )

    assumptions: list[str] = []
    warnings: list[str] = []

    if sum(monthly_heating) <= 0:
        monthly_heating = _monthly_from_annual(
            annual_heating_input,
            shape=[
                0.25,
                0.17,
                0.14,
                0.04,
                0.01,
                0.00,
                0.00,
                0.00,
                0.01,
                0.05,
                0.14,
                0.19,
            ],
        )

        if annual_heating_input > 0:
            assumptions.append(
                "Profil chauffage mensuel reconstruit "
                "depuis la valeur annuelle."
            )

    if sum(monthly_cooling) <= 0:
        annual_cooling_fallback = annual_cooling_input

        if annual_cooling_fallback <= 0:
            annual_cooling_fallback = (
                annual_electricity_kwh * 0.35
            )

            if annual_cooling_fallback > 0:
                assumptions.append(
                    "Besoin de refroidissement estimé à 35 % "
                    "de la consommation électrique annuelle."
                )

        monthly_cooling = _monthly_from_annual(
            annual_cooling_fallback,
            shape=[
                0.00,
                0.00,
                0.01,
                0.02,
                0.06,
                0.10,
                0.14,
                0.17,
                0.34,
                0.12,
                0.03,
                0.01,
            ],
        )

    if sum(monthly_ecs) <= 0:
        annual_ecs_fallback = annual_ecs_input

        if annual_ecs_fallback <= 0:
            annual_ecs_fallback = production_hl * 4.0

            if annual_ecs_fallback > 0:
                assumptions.append(
                    "Besoin ECS estimé à 4 kWh "
                    "par hectolitre produit."
                )

        monthly_ecs = _monthly_from_annual(
            annual_ecs_fallback,
        )

    if sum(monthly_electricity) <= 0:
        monthly_electricity = _monthly_from_annual(
            annual_electricity_kwh,
        )

    annual_heating = sum(monthly_heating)
    annual_cooling = sum(monthly_cooling)
    annual_ecs = sum(monthly_ecs)
    annual_electricity = sum(monthly_electricity)

    heat_recovery = estimate_recoverable_heat(
        monthly_cooling_kwh=monthly_cooling,
        refrigeration_cop=_safe_float(
            data.get("refrigeration_cop"),
            3.0,
        ),
        recovery_efficiency=_safe_float(
            data.get("heat_recovery_efficiency"),
            0.65,
        ),
        source_temperature_c=_safe_float(
            data.get("heat_recovery_temperature_c"),
            35.0,
        ),
    )

    profile_available = (
        annual_heating > 0
        or annual_cooling > 0
        or annual_ecs > 0
    )

    if not profile_available:
        warnings.append(
            "Aucun besoin thermique exploitable n’a été calculé."
        )

    measured_profiles = bool(
        data.get("profiles_calculated")
        or data.get("profile_available")
    )

    quality_score = 85 if measured_profiles else 55

    if assumptions:
        quality_score -= min(
            20,
            len(assumptions) * 5,
        )

    quality_score = max(
        0,
        min(100, quality_score),
    )

    return {
        "schema_version": "1.1",
        "source": "SimulCave",
        "source_format": (
            "calculated_monthly_profile"
            if measured_profiles
            else "estimated_profile"
        ),
        "simulation_scope": "building_only",
        "profile_available": profile_available,

        "monthly_heating_kwh": [
            round(value, 1)
            for value in monthly_heating
        ],
        "monthly_cooling_kwh": [
            round(value, 1)
            for value in monthly_cooling
        ],
        "monthly_ecs_kwh": [
            round(value, 1)
            for value in monthly_ecs
        ],
        "monthly_electricity_kwh": [
            round(value, 1)
            for value in monthly_electricity
        ],
        "monthly_temperature_c": [
            round(value, 1)
            for value in monthly_temperature
        ],
        "monthly_humidity_percent": [
            round(value, 1)
            for value in monthly_humidity
        ],
        "monthly_humidity_risk_index": [
            round(value, 1)
            for value in monthly_humidity_risk
        ],

        "annual_heating_kwh": round(
            annual_heating,
            0,
        ),
        "annual_cooling_kwh": round(
            annual_cooling,
            0,
        ),
        "annual_ecs_kwh": round(
            annual_ecs,
            0,
        ),
        "annual_electricity_kwh": round(
            annual_electricity,
            0,
        ),

        "recommended_hvac_power_kw": (
            _recommended_power_kw(
                monthly_heating,
                monthly_cooling,
            )
        ),

        "thermal_stability_index": (
            _thermal_stability_index(
                monthly_temperature
            )
        ),

        "quality": {
            "score": quality_score,
            "profile_available": profile_available,
            "assumptions": assumptions,
            "warnings": warnings,
        },

        "input_summary": {
            "surface_m2": round(surface_m2, 1),
            "volume_m3": round(volume_m3, 1),
            "production_hl": round(production_hl, 1),
        },
                "heat_recovery": heat_recovery,

        "monthly_recoverable_heat_kwh": (
            heat_recovery[
                "monthly_recoverable_heat_kwh"
            ]
        ),

        "annual_recoverable_heat_kwh": (
            heat_recovery[
                "annual_recoverable_heat_kwh"
            ]
        ),

        "annual_rejected_heat_kwh": (
            heat_recovery[
                "annual_rejected_heat_kwh"
            ]
        ),
    }