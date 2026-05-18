# app/services/simulation.py

from dataclasses import dataclass


OUTDOOR_TEMP_WINTER_C = 0
OUTDOOR_TEMP_SUMMER_C = 30

HEATING_HOURS = 24 * 120
COOLING_HOURS = 24 * 120


@dataclass
class SimulationResult:
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
    heating_kwh = 0
    cooling_kwh = 0
    process_heating_kwh = 0
    process_cooling_kwh = 0

    total_volume = cave_volume(cave)

    for zone in cave.zones:
        process_heating_kwh += zone.process_heating_kwh or 0
        process_cooling_kwh += zone.process_cooling_kwh or 0

        delta_winter = max(zone.target_temp_winter_c - OUTDOOR_TEMP_WINTER_C, 0)
        delta_summer = max(OUTDOOR_TEMP_SUMMER_C - zone.target_temp_summer_c, 0)

        zone_volume_ratio = zone.volume_m3 / total_volume

        for wall in cave.walls:
            effective_area = wall.area_m2 * zone_volume_ratio

            heating_kwh += calculate_transmission_kwh(
                wall.u_value,
                effective_area,
                delta_winter,
                HEATING_HOURS,
                cave.buried_factor,
            )

            cooling_kwh += calculate_transmission_kwh(
                wall.u_value,
                effective_area,
                delta_summer,
                COOLING_HOURS,
                cave.buried_factor,
            )

    return SimulationResult(
        heating_kwh=round(heating_kwh, 1),
        cooling_kwh=round(cooling_kwh, 1),
        process_heating_kwh=round(process_heating_kwh, 1),
        process_cooling_kwh=round(process_cooling_kwh, 1),
        total_heating_kwh=round(heating_kwh + process_heating_kwh, 1),
        total_cooling_kwh=round(cooling_kwh + process_cooling_kwh, 1),
    )