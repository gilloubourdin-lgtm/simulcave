# app/services/weather.py

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean

import requests


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
    weather = WEATHER_DATA.get(region, WEATHER_DATA["Vaud"]).copy()
    weather["source"] = f"région climatique de secours : {region}"
    return weather


def geocode_address(address: str) -> dict | None:
    if not address:
        return None

    # 1) Essai Nominatim / OpenStreetMap pour les vraies adresses
    try:
        nominatim_url = "https://nominatim.openstreetmap.org/search"
        nominatim_params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": "ch",
        }
        headers = {
            "User-Agent": "SimulCave/1.0 (gilles.bourdin@agroscope.admin.ch)"
        }

        response = requests.get(
            nominatim_url,
            params=nominatim_params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()

        results = response.json()

        if results:
            place = results[0]
            return {
                "latitude": float(place["lat"]),
                "longitude": float(place["lon"]),
                "name": place.get("display_name"),
                "country": "Switzerland",
                "admin1": None,
            }

    except Exception:
        pass

    # 2) Secours Open-Meteo pour ville / localité / code postal
    try:
        open_meteo_url = "https://geocoding-api.open-meteo.com/v1/search"
        open_meteo_params = {
            "name": address,
            "count": 1,
            "language": "fr",
            "format": "json",
            "countryCode": "CH",
        }

        response = requests.get(
            open_meteo_url,
            params=open_meteo_params,
            timeout=10,
        )
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

    except Exception:
        return None


def get_dynamic_weather_monthly(latitude: float, longitude: float) -> dict:
    today = date.today()

    # Dernière année complète disponible jusqu’à hier
    end_date = today - timedelta(days=1)
    start_date = end_date - timedelta(days=365)

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_mean",
        "timezone": "Europe/Zurich",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    temps = daily.get("temperature_2m_mean", [])

    if not dates or not temps:
        raise ValueError("Aucune donnée météo historique Open-Meteo reçue.")

    by_month = defaultdict(list)

    for day, temp in zip(dates, temps):
        if temp is None:
            continue

        month = int(day[5:7])
        by_month[month].append(temp)

    monthly_temps = []

    for month in range(1, 13):
        values = by_month.get(month, [])

        if values:
            monthly_temps.append(round(mean(values), 1))
        else:
            monthly_temps.append(get_weather_for_region("Vaud")["temps"][month - 1])

    return {
        "temps": monthly_temps,
        "source": "Open-Meteo historique 12 mois",
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