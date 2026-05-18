# app/services/simulation.py

from dataclasses import dataclass

from app.services.weather import MONTHS, HOURS_PER_MONTH, get_weather_for_region


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


def simulate_cave(cave) -> SimulationResult:
    weather = get_weather_for_region(cave.region)
    monthly_temps = weather["temps"]

    monthly_results = []

    total_heating = 0
    total_cooling = 0
    process_heating = 0
    process_cooling = 0

    total_volume = cave_volume(cave)

    for month_index, outdoor_temp in enumerate(monthly_temps):
        month_heating = 0
        month_cooling = 0
        hours = HOURS_PER_MONTH[month_index]

        for zone in cave.zones:
            zone_ratio = zone.volume_m3 / total_volume

            process_heating += (zone.process_heating_kwh or 0) / 12
            process_cooling += (zone.process_cooling_kwh or 0) / 12

            target_heating = zone.target_temp_winter_c
            target_cooling = zone.target_temp_summer_c

            delta_heating = max(target_heating - outdoor_temp, 0)
            delta_cooling = max(outdoor_temp - target_cooling, 0)

            for wall in cave.walls:
                effective_area = wall.area_m2 * zone_ratio

                month_heating += calculate_transmission_kwh(
                    u_value=wall.u_value,
                    area_m2=effective_area,
                    delta_t=delta_heating,
                    hours=hours,
                    buried_factor=cave.buried_factor,
                )

                month_cooling += calculate_transmission_kwh(
                    u_value=wall.u_value,
                    area_m2=effective_area,
                    delta_t=delta_cooling,
                    hours=hours,
                    buried_factor=cave.buried_factor,
                )

        total_heating += month_heating
        total_cooling += month_cooling

        monthly_results.append(
            MonthlyResult(
                month=MONTHS[month_index],
                outdoor_temp_c=outdoor_temp,
                heating_kwh=round(month_heating, 1),
                cooling_kwh=round(month_cooling, 1),
            )
        )

    return SimulationResult(
        monthly_results=monthly_results,
        heating_kwh=round(total_heating, 1),
        cooling_kwh=round(total_cooling, 1),
        process_heating_kwh=round(process_heating, 1),
        process_cooling_kwh=round(process_cooling, 1),
        total_heating_kwh=round(total_heating + process_heating, 1),
        total_cooling_kwh=round(total_cooling + process_cooling, 1),
    )