# app/simulcave_core/heat_recovery.py

from __future__ import annotations

from typing import Any


DEFAULT_RECOVERY_EFFICIENCY = 0.65
DEFAULT_REJECTION_RATIO = 1.20
DEFAULT_SOURCE_TEMPERATURE_C = 35.0


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
    values: Any,
) -> list[float]:
    if not isinstance(values, (list, tuple)):
        return [0.0] * 12

    result = [
        max(0.0, _safe_float(value))
        for value in list(values)[:12]
    ]

    while len(result) < 12:
        result.append(0.0)

    return result


def estimate_recoverable_heat(
    *,
    monthly_cooling_kwh: list[float],
    refrigeration_cop: float = 3.0,
    recovery_efficiency: float = DEFAULT_RECOVERY_EFFICIENCY,
    source_temperature_c: float = DEFAULT_SOURCE_TEMPERATURE_C,
) -> dict:
    """
    Estime la chaleur rejetée et la chaleur techniquement récupérable
    par un système frigorifique.

    Hypothèse thermodynamique simplifiée :

        chaleur rejetée =
            froid utile + électricité compresseur

        électricité compresseur =
            froid utile / COP

    La chaleur récupérable est ensuite limitée par le rendement
    de récupération du condenseur et du circuit hydraulique.
    """

    cooling = _safe_monthly(
        monthly_cooling_kwh
    )

    cop = max(
        1.0,
        _safe_float(
            refrigeration_cop,
            3.0,
        ),
    )

    efficiency = min(
        1.0,
        max(
            0.0,
            _safe_float(
                recovery_efficiency,
                DEFAULT_RECOVERY_EFFICIENCY,
            ),
        ),
    )

    source_temperature = max(
        0.0,
        _safe_float(
            source_temperature_c,
            DEFAULT_SOURCE_TEMPERATURE_C,
        ),
    )

    monthly_compressor_electricity = [
        value / cop
        for value in cooling
    ]

    monthly_rejected_heat = [
        cooling[index]
        + monthly_compressor_electricity[index]
        for index in range(12)
    ]

    monthly_recoverable_heat = [
        value * efficiency
        for value in monthly_rejected_heat
    ]

    annual_cooling = sum(cooling)
    annual_compressor_electricity = sum(
        monthly_compressor_electricity
    )
    annual_rejected_heat = sum(
        monthly_rejected_heat
    )
    annual_recoverable_heat = sum(
        monthly_recoverable_heat
    )

    available = (
        annual_recoverable_heat > 0
    )

    if not available:
        confidence = 0.0
        message = (
            "Aucun besoin frigorifique exploitable : "
            "aucune chaleur récupérable calculée."
        )

    elif annual_cooling < 5000:
        confidence = 0.55
        message = (
            "Potentiel de récupération faible à modéré. "
            "À confirmer avec la puissance et les heures "
            "de fonctionnement du groupe froid."
        )

    else:
        confidence = 0.75
        message = (
            "Potentiel de récupération calculé depuis "
            "les besoins frigorifiques mensuels."
        )

    return {
        "available": available,
        "source_type": "refrigeration_condenser",

        "monthly_cooling_kwh": [
            round(value, 1)
            for value in cooling
        ],

        "monthly_compressor_electricity_kwh": [
            round(value, 1)
            for value in monthly_compressor_electricity
        ],

        "monthly_rejected_heat_kwh": [
            round(value, 1)
            for value in monthly_rejected_heat
        ],

        "monthly_recoverable_heat_kwh": [
            round(value, 1)
            for value in monthly_recoverable_heat
        ],

        "annual_cooling_kwh": round(
            annual_cooling,
            0,
        ),

        "annual_compressor_electricity_kwh": round(
            annual_compressor_electricity,
            0,
        ),

        "annual_rejected_heat_kwh": round(
            annual_rejected_heat,
            0,
        ),

        "annual_recoverable_heat_kwh": round(
            annual_recoverable_heat,
            0,
        ),

        "refrigeration_cop": round(
            cop,
            2,
        ),

        "recovery_efficiency": round(
            efficiency,
            3,
        ),

        "source_temperature_c": round(
            source_temperature,
            1,
        ),

        "confidence": round(
            confidence,
            2,
        ),

        "estimated": True,
        "message": message,

        "assumptions": [
            (
                "La chaleur rejetée est estimée comme la somme "
                "du froid utile et de l’électricité du compresseur."
            ),
            (
                f"COP frigorifique utilisé : {cop:.2f}."
            ),
            (
                "Rendement global de récupération utilisé : "
                f"{efficiency * 100:.0f} %."
            ),
        ],
    }