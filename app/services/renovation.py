from dataclasses import dataclass
from copy import deepcopy

from app.services.simulation import simulate_cave


ENERGY_PRICE_CHF_PER_KWH = 0.24
CO2_FACTOR_KG_PER_KWH = 0.09


@dataclass
class RenovationScenario:
    name: str
    description: str
    investment_chf: float
    heating_kwh_before: float
    cooling_kwh_before: float
    heating_kwh_after: float
    cooling_kwh_after: float
    energy_saved_kwh: float
    money_saved_chf: float
    co2_saved_kg: float
    payback_years: float | None


def apply_u_value_reduction(cave, wall_filter, reduction_factor: float):
    # Force le chargement SQLAlchemy avant deepcopy
    list(cave.walls)
    list(cave.zones)

    for zone in cave.zones:
        if hasattr(zone, "monthly_targets"):
            list(zone.monthly_targets)

    cave_copy = deepcopy(cave)

    for wall in cave_copy.walls:
        if wall_filter(wall):
            wall.u_value = wall.u_value * reduction_factor

    return cave_copy


def apply_ventilation_optimization(
    cave,
    target_ventilation_rate_ach: float = 0.05,
):
    cave_copy = deepcopy(cave)

    cave_copy.ventilation_enabled = True
    cave_copy.ventilation_rate_ach = target_ventilation_rate_ach

    return cave_copy


def build_scenario_result(
    cave,
    renovated_cave,
    name: str,
    description: str,
    investment_chf: float,
) -> RenovationScenario:
    before = simulate_cave(cave)
    after = simulate_cave(renovated_cave)

    before_energy = before.total_heating_kwh + before.total_cooling_kwh
    after_energy = after.total_heating_kwh + after.total_cooling_kwh

    energy_saved = max(before_energy - after_energy, 0)
    money_saved = energy_saved * ENERGY_PRICE_CHF_PER_KWH
    co2_saved = energy_saved * CO2_FACTOR_KG_PER_KWH

    payback = None
    if money_saved > 0:
        payback = investment_chf / money_saved

    return RenovationScenario(
        name=name,
        description=description,
        investment_chf=round(investment_chf, 0),
        heating_kwh_before=before.total_heating_kwh,
        cooling_kwh_before=before.total_cooling_kwh,
        heating_kwh_after=after.total_heating_kwh,
        cooling_kwh_after=after.total_cooling_kwh,
        energy_saved_kwh=round(energy_saved, 1),
        money_saved_chf=round(money_saved, 0),
        co2_saved_kg=round(co2_saved, 1),
        payback_years=round(payback, 1) if payback else None,
    )


def calculate_scenario(
    cave,
    name: str,
    description: str,
    investment_chf: float,
    wall_filter,
    reduction_factor: float,
) -> RenovationScenario:
    renovated_cave = apply_u_value_reduction(
        cave=cave,
        wall_filter=wall_filter,
        reduction_factor=reduction_factor,
    )

    return build_scenario_result(
        cave=cave,
        renovated_cave=renovated_cave,
        name=name,
        description=description,
        investment_chf=investment_chf,
    )


def calculate_ventilation_scenario(
    cave,
    target_ventilation_rate_ach: float = 0.05,
    investment_chf: float = 5000,
) -> RenovationScenario:
    current_rate = getattr(cave, "ventilation_rate_ach", 0.10) or 0.10

    renovated_cave = apply_ventilation_optimization(
        cave=cave,
        target_ventilation_rate_ach=target_ventilation_rate_ach,
    )

    return build_scenario_result(
        cave=cave,
        renovated_cave=renovated_cave,
        name="Ventilation optimisée",
        description=(
            "Réduction des pertes liées au renouvellement d’air "
            f"par meilleure étanchéité ou pilotage de la ventilation "
            f"({current_rate:.2f} → {target_ventilation_rate_ach:.2f} vol/h)."
        ),
        investment_chf=investment_chf,
    )


def generate_renovation_scenarios(cave) -> list[RenovationScenario]:
    return [
        calculate_scenario(
            cave=cave,
            name="Isolation toiture",
            description="Réduction de 40 % de la valeur U de la toiture.",
            investment_chf=18000,
            wall_filter=lambda wall: wall.name == "Toiture",
            reduction_factor=0.60,
        ),
        calculate_scenario(
            cave=cave,
            name="Isolation murs",
            description="Réduction de 35 % de la valeur U des murs verticaux.",
            investment_chf=35000,
            wall_filter=lambda wall: wall.orientation in ["N", "S", "E", "O"],
            reduction_factor=0.65,
        ),
        calculate_scenario(
            cave=cave,
            name="Isolation complète",
            description="Réduction de 45 % de la valeur U des murs, toiture et sol.",
            investment_chf=65000,
            wall_filter=lambda wall: True,
            reduction_factor=0.55,
        ),
        calculate_ventilation_scenario(
            cave=cave,
            target_ventilation_rate_ach=0.05,
            investment_chf=5000,
        ),
    ]