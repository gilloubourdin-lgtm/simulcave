# app/services/simulation.py

from dataclasses import dataclass

from app.services.weather import MONTHS, HOURS_PER_MONTH, get_weather_for_cave


@dataclass
class MonthlyResult:
    month: str
    outdoor_temp_c: float
    effective_temp_c: float
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
    soil_temperature_c: float


def cave_volume(cave) -> float:
    volume = cave.length_m * cave.width_m * cave.height_m
    return max(volume, 1)


def calculate_transmission_kwh(
    u_value: float,
    area_m2: float,
    delta_t: float,
    hours: float,
) -> float:
    wh = u_value * area_m2 * delta_t * hours
    return wh / 1000


def month_is_active(month_number: int, start_month: int, end_month: int) -> bool:
    if start_month <= end_month:
        return start_month <= month_number <= end_month

    return month_number >= start_month or month_number <= end_month


def active_month_count(start_month: int, end_month: int) -> int:
    return sum(
        1 for month in range(1, 13)
        if month_is_active(month, start_month, end_month)
    )


def calculate_effective_outdoor_temp(
    outdoor_temp: float,
    soil_temp: float,
    buried_factor: float,
) -> float:
    buried_factor = max(0, min(buried_factor, 1))

    return (
        outdoor_temp * (1 - buried_factor)
        + soil_temp * buried_factor
    )


def simulate_cave(cave) -> SimulationResult:
    weather = get_weather_for_cave(cave)
    monthly_temps = weather["temps"]
    weather_source = weather.get("source", "région climatique de secours")

    annual_mean_temp = sum(monthly_temps) / len(monthly_temps)
    soil_temp = annual_mean_temp + 2

    monthly_results = []

    total_envelope_heating = 0
    total_envelope_cooling = 0
    total_process_heating = 0
    total_process_cooling = 0

    total_volume = cave_volume(cave)

    for month_index, outdoor_temp in enumerate(monthly_temps):
        month_number = month_index + 1
        hours = HOURS_PER_MONTH[month_index]

        effective_outdoor_temp = calculate_effective_outdoor_temp(
            outdoor_temp=outdoor_temp,
            soil_temp=soil_temp,
            buried_factor=cave.buried_factor,
        )

        month_envelope_heating = 0
        month_envelope_cooling = 0
        month_process_heating = 0
        month_process_cooling = 0

        for zone in cave.zones:
            zone_ratio = zone.volume_m3 / total_volume

            heating_start = getattr(zone, "process_heating_start_month", 1) or 1
            heating_end = getattr(zone, "process_heating_end_month", 12) or 12
            cooling_start = getattr(zone, "process_cooling_start_month", 1) or 1
            cooling_end = getattr(zone, "process_cooling_end_month", 12) or 12

            heating_months = active_month_count(heating_start, heating_end)
            cooling_months = active_month_count(cooling_start, cooling_end)

            if heating_months > 0 and month_is_active(
                month_number,
                heating_start,
                heating_end,
            ):
                month_process_heating += (
                    (zone.process_heating_kwh or 0) / heating_months
                )

            if cooling_months > 0 and month_is_active(
                month_number,
                cooling_start,
                cooling_end,
            ):
                month_process_cooling += (
                    (zone.process_cooling_kwh or 0) / cooling_months
                )

            target_heating = zone.target_temp_winter_c
            target_cooling = zone.target_temp_summer_c

            delta_heating = max(target_heating - effective_outdoor_temp, 0)
            delta_cooling = max(effective_outdoor_temp - target_cooling, 0)

            for wall in cave.walls:
                effective_area = wall.area_m2 * zone_ratio
                inertia_factor = getattr(wall, "inertia_factor", 1.0) or 1.0

                month_envelope_heating += (
                    calculate_transmission_kwh(
                        u_value=wall.u_value,
                        area_m2=effective_area,
                        delta_t=delta_heating,
                        hours=hours,
                    )
                    * inertia_factor
                )

                month_envelope_cooling += (
                    calculate_transmission_kwh(
                        u_value=wall.u_value,
                        area_m2=effective_area,
                        delta_t=delta_cooling,
                        hours=hours,
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
                outdoor_temp_c=round(outdoor_temp, 1),
                effective_temp_c=round(effective_outdoor_temp, 1),
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
        weather_source=weather_source,
        soil_temperature_c=round(soil_temp, 1),
    )