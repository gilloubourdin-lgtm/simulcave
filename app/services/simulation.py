# app/services/simulation.py

from dataclasses import dataclass

from app.services.weather import MONTHS, HOURS_PER_MONTH, get_weather_for_cave
from app.services.energy_factors import get_energy_price, get_co2_factor


ENERGY_SOURCE = "electricity"


@dataclass
class MonthlyResult:
    month: str
    outdoor_temp_c: float
    heating_kwh: float
    cooling_kwh: float


@dataclass
class SimulationResult:
    monthly_results: list[MonthlyResult]

    heating_kwh: float
    cooling_kwh: float
    process_heating_kwh: float
    process_cooling_kwh: float

    total_heating_kwh: float
    total_cooling_kwh: float
    total_energy_kwh: float

    annual_cost_chf: float
    annual_co2_kg: float
    annual_co2_tons: float

    weather_source: str


def cave_volume(cave) -> float:
    volume = cave.length_m * cave.width_m * cave.height_m
    return max(volume, 1)


def calculate_transmission_kwh(
    u_value: float,
    area_m2: float,
    delta_t: float,
    hours: float,
    buried_factor: float,
) -> float:
    wh = u_value * area_m2 * delta_t * hours * buried_factor
    return wh / 1000


def month_is_active(month_number: int, start_month: int, end_month: int) -> bool:
    if start_month <= end_month:
        return start_month <= month_number <= end_month
    return month_number >= start_month or month_number <= end_month


def active_month_count(start_month: int, end_month: int) -> int:
    return sum(
        1 for m in range(1, 13)
        if month_is_active(m, start_month, end_month)
    )


def simulate_cave(cave) -> SimulationResult:
    weather = get_weather_for_cave(cave)
    monthly_temps = weather["temps"]
    weather_source = weather.get("source", "région climatique de secours")

    monthly_results = []

    total_envelope_heating = 0
    total_envelope_cooling = 0
    total_process_heating = 0
    total_process_cooling = 0

    total_volume = cave_volume(cave)

    for month_index, outdoor_temp in enumerate(monthly_temps):
        month_number = month_index + 1
        month_envelope_heating = 0
        month_envelope_cooling = 0
        month_process_heating = 0
        month_process_cooling = 0

        hours = HOURS_PER_MONTH[month_index]

        for zone in cave.zones:
            zone_ratio = zone.volume_m3 / total_volume

            heating_start = getattr(zone, "process_heating_start_month", 1) or 1
            heating_end = getattr(zone, "process_heating_end_month", 12) or 12
            cooling_start = getattr(zone, "process_cooling_start_month", 1) or 1
            cooling_end = getattr(zone, "process_cooling_end_month", 12) or 12

            heating_months = active_month_count(heating_start, heating_end)
            cooling_months = active_month_count(cooling_start, cooling_end)

            if heating_months > 0 and month_is_active(month_number, heating_start, heating_end):
                month_process_heating += (zone.process_heating_kwh or 0) / heating_months

            if cooling_months > 0 and month_is_active(month_number, cooling_start, cooling_end):
                month_process_cooling += (zone.process_cooling_kwh or 0) / cooling_months

            target_heating = zone.target_temp_winter_c
            target_cooling = zone.target_temp_summer_c

            delta_heating = max(target_heating - outdoor_temp, 0)
            delta_cooling = max(outdoor_temp - target_cooling, 0)

            for wall in cave.walls:
                effective_area = wall.area_m2 * zone_ratio
                inertia_factor = getattr(wall, "inertia_factor", 1.0) or 1.0

                month_envelope_heating += (
                    calculate_transmission_kwh(
                        u_value=wall.u_value,
                        area_m2=effective_area,
                        delta_t=delta_heating,
                        hours=hours,
                        buried_factor=cave.buried_factor,
                    )
                    * inertia_factor
                )

                month_envelope_cooling += (
                    calculate_transmission_kwh(
                        u_value=wall.u_value,
                        area_m2=effective_area,
                        delta_t=delta_cooling,
                        hours=hours,
                        buried_factor=cave.buried_factor,
                    )
                    * inertia_factor
                )

        month_total_heating = month_envelope_heating + month_process_heating
        month_total_cooling = month_envelope_cooling + month_process_cooling

        total_envelope_heating += month_envelope_heating
        total_envelope_cooling += month_envelope_cooling
        total_process_heating += month_process_heating
        total_process_cooling += month_process_cooling

        monthly_results.append(
            MonthlyResult(
                month=MONTHS[month_index],
                outdoor_temp_c=outdoor_temp,
                heating_kwh=round(month_total_heating, 1),
                cooling_kwh=round(month_total_cooling, 1),
            )
        )

    total_heating = total_envelope_heating + total_process_heating
    total_cooling = total_envelope_cooling + total_process_cooling
    total_energy = total_heating + total_cooling

    annual_cost = total_energy * cave.energy_price_chf_per_kwh
    annual_co2_kg = total_energy * cave.co2_factor_kg_per_kwh
    annual_co2_tons = annual_co2_kg / 1000

    return SimulationResult(
        monthly_results=monthly_results,
        weather_source=weather_source,
        heating_kwh=round(total_envelope_heating, 1),
        cooling_kwh=round(total_envelope_cooling, 1),
        process_heating_kwh=round(total_process_heating, 1),
        process_cooling_kwh=round(total_process_cooling, 1),
        total_heating_kwh=round(total_heating, 1),
        total_cooling_kwh=round(total_cooling, 1),
        total_energy_kwh=round(total_energy, 1),
        annual_cost_chf=round(annual_cost, 1),
        annual_co2_kg=round(annual_co2_kg, 1),
        annual_co2_tons=round(annual_co2_tons, 2),
    )