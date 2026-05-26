from dataclasses import dataclass
import math
from app.services.weather import MONTHS, HOURS_PER_MONTH, get_weather_for_cave


@dataclass
class MonthlyResult:
    month: str
    outdoor_temp_c: float
    effective_temp_c: float
    heating_kwh: float
    cooling_kwh: float
    ventilation_heating_kwh: float
    ventilation_cooling_kwh: float
    dew_point_c: float
    condensation_risk: str
    relative_humidity_percent: float
    humidity_risk_index: float
    humidity_stability_label: str


@dataclass
class WallResult:
    wall_name: str
    orientation: str
    material: str
    heating_kwh: float
    cooling_kwh: float
    total_kwh: float


@dataclass
class SimulationResult:
    monthly_results: list[MonthlyResult]

    heating_kwh: float
    cooling_kwh: float
    process_heating_kwh: float
    process_cooling_kwh: float
    ventilation_heating_kwh: float
    ventilation_cooling_kwh: float

    total_heating_kwh: float
    total_cooling_kwh: float
    total_energy_kwh: float

    annual_cost_chf: float
    annual_co2_kg: float
    annual_co2_tons: float

    weather_source: str
    soil_temperature_c: float

    wall_results: list[WallResult]


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


def calculate_ventilation_load_kwh(
    volume_m3: float,
    air_changes_per_hour: float,
    indoor_temp_c: float,
    outdoor_temp_c: float,
    hours: float,
) -> float:
    delta_t = abs(indoor_temp_c - outdoor_temp_c)
    airflow_m3_h = volume_m3 * air_changes_per_hour
    return 0.34 * airflow_m3_h * delta_t * hours / 1000


def month_is_active(month_number: int, start_month: int, end_month: int) -> bool:
    if start_month <= end_month:
        return start_month <= month_number <= end_month

    return month_number >= start_month or month_number <= end_month


def active_month_count(start_month: int, end_month: int) -> int:
    return sum(
        1 for month in range(1, 13)
        if month_is_active(month, start_month, end_month)
    )


def wall_external_temperature(
    wall,
    outdoor_temp: float,
    soil_temp: float,
    buried_factor: float,
) -> float:
    buried_factor = max(0, min(buried_factor, 1))

    if wall.name == "Toiture" or wall.orientation == "H":
        return outdoor_temp

    if wall.name == "Sol" or wall.orientation == "B":
        return soil_temp

    return outdoor_temp * (1 - buried_factor) + soil_temp * buried_factor

def dew_point_c(temperature_c: float, relative_humidity_pct: float) -> float:
    """
    Calcule le point de rosée en °C avec la formule de Magnus.
    """
    rh = max(1, min(relative_humidity_pct, 100)) / 100
    a = 17.62
    b = 243.12

    gamma = (a * temperature_c / (b + temperature_c)) + math.log(rh)
    return (b * gamma) / (a - gamma)


def condensation_risk_level(
    surface_temp_c: float,
    dew_point_temp_c: float,
) -> str:
    """
    Évalue le risque de condensation.
    """
    margin = surface_temp_c - dew_point_temp_c

    if margin <= 0:
        return "élevé"
    if margin <= 2:
        return "moyen"
    return "faible"

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
    total_ventilation_heating = 0
    total_ventilation_cooling = 0

    total_volume = cave_volume(cave)

    wall_totals = {}

    for wall in cave.walls:
        wall_totals[wall.id] = {
            "wall": wall,
            "heating": 0,
            "cooling": 0,
        }

    for month_index, outdoor_temp in enumerate(monthly_temps):
        month_number = month_index + 1
        hours = HOURS_PER_MONTH[month_index]

        month_envelope_heating = 0
        month_envelope_cooling = 0
        month_process_heating = 0
        month_process_cooling = 0
        month_ventilation_heating = 0
        month_ventilation_cooling = 0

        effective_temperatures = []

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

            if getattr(cave, "ventilation_enabled", True):
                zone_volume = zone.volume_m3 or (total_volume * zone_ratio)
                ach = getattr(cave, "ventilation_rate_ach", 0.2) or 0.2

                if outdoor_temp < target_heating:
                    month_ventilation_heating += calculate_ventilation_load_kwh(
                        volume_m3=zone_volume,
                        air_changes_per_hour=ach,
                        indoor_temp_c=target_heating,
                        outdoor_temp_c=outdoor_temp,
                        hours=hours,
                    )

                elif outdoor_temp > target_cooling:
                    month_ventilation_cooling += calculate_ventilation_load_kwh(
                        volume_m3=zone_volume,
                        air_changes_per_hour=ach,
                        indoor_temp_c=target_cooling,
                        outdoor_temp_c=outdoor_temp,
                        hours=hours,
                    )

            for wall in cave.walls:
                wall_temp = wall_external_temperature(
                    wall=wall,
                    outdoor_temp=outdoor_temp,
                    soil_temp=soil_temp,
                    buried_factor=cave.buried_factor,
                )

                effective_temperatures.append(wall_temp)

                delta_heating = max(target_heating - wall_temp, 0)
                delta_cooling = max(wall_temp - target_cooling, 0)

                effective_area = wall.area_m2 * zone_ratio
                inertia_factor = getattr(wall, "inertia_factor", 1.0) or 1.0

                wall_heating = (
                    calculate_transmission_kwh(
                        u_value=wall.u_value,
                        area_m2=effective_area,
                        delta_t=delta_heating,
                        hours=hours,
                    )
                    * inertia_factor
                )

                wall_cooling = (
                    calculate_transmission_kwh(
                        u_value=wall.u_value,
                        area_m2=effective_area,
                        delta_t=delta_cooling,
                        hours=hours,
                    )
                    * inertia_factor
                )

                month_envelope_heating += wall_heating
                month_envelope_cooling += wall_cooling

                wall_totals[wall.id]["heating"] += wall_heating
                wall_totals[wall.id]["cooling"] += wall_cooling

        month_total_heating = (
            month_envelope_heating
            + month_process_heating
            + month_ventilation_heating
        )

        month_total_cooling = (
            month_envelope_cooling
            + month_process_cooling
            + month_ventilation_cooling
        )

        total_envelope_heating += month_envelope_heating
        total_envelope_cooling += month_envelope_cooling
        total_process_heating += month_process_heating
        total_process_cooling += month_process_cooling
        total_ventilation_heating += month_ventilation_heating
        total_ventilation_cooling += month_ventilation_cooling

        if effective_temperatures:
            effective_temp = sum(effective_temperatures) / len(effective_temperatures)
        else:
            effective_temp = outdoor_temp

        base_humidity_values = [
            getattr(zone, "target_humidity_percent", 75) or 75
            for zone in cave.zones
        ]

        base_humidity = (
            sum(base_humidity_values) / len(base_humidity_values)
            if base_humidity_values
            else 75
        )

        avg_humidity = (
            base_humidity
            - ((effective_temp - 12.0) * 1.8)
        )

        avg_humidity = max(55.0, min(95.0, avg_humidity))

        humidity_risk_index = 0.0

        if avg_humidity < 65:
            humidity_risk_index += 0.6

        if avg_humidity > 90:
            humidity_risk_index += 0.5

        if effective_temp > 18:
            humidity_risk_index += 0.2

        humidity_risk_index = max(0.0, min(1.0, humidity_risk_index))

        if humidity_risk_index >= 0.6:
            humidity_stability_label = "critique"
        elif humidity_risk_index >= 0.3:
            humidity_stability_label = "à surveiller"
        else:
            humidity_stability_label = "stable"

        avg_humidity = (
            sum(humidity_values) / len(humidity_values)
            if humidity_values
            else 75
        )

        dew_point = dew_point_c(
            temperature_c=effective_temp,
            relative_humidity_pct=avg_humidity,
        )

        condensation_risk = condensation_risk_level(
            surface_temp_c=effective_temp,
            dew_point_temp_c=dew_point,
        )

        monthly_results.append(
            MonthlyResult(
                month=MONTHS[month_index],
                outdoor_temp_c=round(outdoor_temp, 1),
                effective_temp_c=round(effective_temp, 1),
                heating_kwh=round(month_total_heating, 1),
                cooling_kwh=round(month_total_cooling, 1),
                ventilation_heating_kwh=round(month_ventilation_heating, 1),
                ventilation_cooling_kwh=round(month_ventilation_cooling, 1),
                dew_point_c=round(dew_point, 1),
                condensation_risk=condensation_risk,
                relative_humidity_percent=round(avg_humidity, 1),
                humidity_risk_index=round(humidity_risk_index, 3),
                humidity_stability_label=humidity_stability_label,
            )
        )

    total_heating = (
        total_envelope_heating
        + total_process_heating
        + total_ventilation_heating
    )

    total_cooling = (
        total_envelope_cooling
        + total_process_cooling
        + total_ventilation_cooling
    )

    total_energy = total_heating + total_cooling

    annual_cost = total_energy * cave.energy_price_chf_per_kwh
    annual_co2_kg = total_energy * cave.co2_factor_kg_per_kwh
    annual_co2_tons = annual_co2_kg / 1000

    wall_results = []

    for item in wall_totals.values():
        wall = item["wall"]
        heating = item["heating"]
        cooling = item["cooling"]

        wall_results.append(
            WallResult(
                wall_name=wall.name,
                orientation=wall.orientation,
                material=wall.material,
                heating_kwh=round(heating, 1),
                cooling_kwh=round(cooling, 1),
                total_kwh=round(heating + cooling, 1),
            )
        )

    return SimulationResult(
        monthly_results=monthly_results,
        heating_kwh=round(total_envelope_heating, 1),
        cooling_kwh=round(total_envelope_cooling, 1),
        process_heating_kwh=round(total_process_heating, 1),
        process_cooling_kwh=round(total_process_cooling, 1),
        ventilation_heating_kwh=round(total_ventilation_heating, 1),
        ventilation_cooling_kwh=round(total_ventilation_cooling, 1),
        total_heating_kwh=round(total_heating, 1),
        total_cooling_kwh=round(total_cooling, 1),
        total_energy_kwh=round(total_energy, 1),
        annual_cost_chf=round(annual_cost, 1),
        annual_co2_kg=round(annual_co2_kg, 1),
        annual_co2_tons=round(annual_co2_tons, 2),
        weather_source=weather_source,
        soil_temperature_c=round(soil_temp, 1),
        wall_results=wall_results,
    )