# app/services/weather.py

import requests
from statistics import mean

MONTHS = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
    "Juil", "Août", "Sep", "Oct", "Nov", "Déc"
]

HOURS_PER_MONTH = [
    744, 672, 744, 720, 744, 720,
    744, 744, 720, 744, 720, 744
]

WEATHER_DATA = {
    "Vaud": {"temps": [2, 3, 6, 10, 14, 18, 21, 20, 16, 11, 6, 3]},
    "Genève": {"temps": [3, 4, 7, 11, 15, 19, 22, 21, 17, 12, 7, 4]},
    "Valais": {"temps": [1, 3, 7, 12, 16, 20, 23, 22, 17, 11, 5, 2]},
    "Fribourg": {"temps": [1, 2, 5, 9, 13, 17, 20, 19, 15, 10, 5, 2]},
    "Tessin": {"temps": [5, 7, 10, 14, 18, 22, 25, 24, 20, 15, 10, 6]},
    "Zurich": {"temps": [1, 2, 6, 10, 14, 18, 21, 20, 16, 10, 5, 2]},
    "Alpes": {"temps": [-3, -2, 1, 5, 9, 13, 16, 15, 11, 6, 1, -2]},
}


def get_weather_for_region(region: str) -> dict:
    return WEATHER_DATA.get(region, WEATHER_DATA["Vaud"])


def geocode_address(address: str) -> dict | None:
    if not address:
        return None

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": address,
        "count": 1,
        "language": "fr",
        "format": "json",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    if not results:
        return None

    place = results[0]

    return {
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "name": place.get("name"),
        "country": place.get("country"),
        "admin1": place.get("admin1"),
    }


def get_dynamic_weather_monthly(latitude: float, longitude: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m",
        "forecast_days": 16,
        "timezone": "Europe/Zurich",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    temps = data.get("hourly", {}).get("temperature_2m", [])

    if not temps:
        raise ValueError("Aucune donnée météo Open-Meteo reçue.")

    avg_temp = round(mean(temps), 1)

    # Forecast 16 jours : on l’utilise comme température dynamique du mois courant.
    # Pour les autres mois, fallback météo régionale.
    monthly_temps = [avg_temp] * 12

    return {
        "temps": monthly_temps,
        "source": "open-meteo",
        "dynamic_avg_temp": avg_temp,
    }


def get_weather_for_cave(cave) -> dict:
    if (
        getattr(cave, "use_dynamic_weather", False)
        and cave.latitude is not None
        and cave.longitude is not None
    ):
        try:
            return get_dynamic_weather_monthly(cave.latitude, cave.longitude)
        except Exception:
            return get_weather_for_region(cave.region)

    return get_weather_for_region(cave.region)