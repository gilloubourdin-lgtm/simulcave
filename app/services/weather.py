# app/services/weather.py

MONTHS = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
    "Juil", "Août", "Sep", "Oct", "Nov", "Déc"
]

HOURS_PER_MONTH = [
    744, 672, 744, 720, 744, 720,
    744, 744, 720, 744, 720, 744
]

WEATHER_DATA = {
    "Vaud": {
        "temps": [2, 3, 6, 10, 14, 18, 21, 20, 16, 11, 6, 3],
        "ground": [8, 8, 9, 10, 12, 14, 16, 17, 16, 14, 11, 9],
        "humidity": [82, 78, 74, 70, 68, 66, 64, 66, 72, 78, 82, 84],
    },
    "Genève": {
        "temps": [3, 4, 7, 11, 15, 19, 22, 21, 17, 12, 7, 4],
        "ground": [8, 8, 9, 11, 13, 15, 17, 18, 17, 14, 11, 9],
        "humidity": [80, 76, 72, 68, 66, 64, 62, 64, 70, 76, 80, 82],
    },
    "Valais": {
        "temps": [1, 3, 7, 12, 16, 20, 23, 22, 17, 11, 5, 2],
        "ground": [7, 8, 9, 11, 14, 16, 18, 18, 16, 13, 10, 8],
        "humidity": [72, 68, 64, 60, 58, 56, 54, 56, 62, 68, 72, 74],
    },
    "Fribourg": {
        "temps": [1, 2, 5, 9, 13, 17, 20, 19, 15, 10, 5, 2],
        "ground": [7, 7, 8, 10, 12, 14, 16, 16, 15, 12, 10, 8],
        "humidity": [84, 80, 76, 72, 70, 68, 66, 68, 74, 80, 84, 86],
    },
    "Tessin": {
        "temps": [5, 7, 10, 14, 18, 22, 25, 24, 20, 15, 10, 6],
        "ground": [10, 10, 11, 13, 15, 17, 19, 20, 18, 16, 13, 11],
        "humidity": [76, 72, 70, 68, 70, 72, 74, 74, 76, 78, 78, 78],
    },
    "Zurich": {
        "temps": [1, 2, 6, 10, 14, 18, 21, 20, 16, 10, 5, 2],
        "ground": [7, 7, 8, 10, 12, 14, 16, 17, 15, 12, 10, 8],
        "humidity": [84, 80, 76, 72, 70, 68, 66, 68, 74, 80, 84, 86],
    },
    "Alpes": {
        "temps": [-3, -2, 1, 5, 9, 13, 16, 15, 11, 6, 1, -2],
        "ground": [4, 4, 5, 7, 9, 11, 13, 13, 11, 8, 6, 5],
        "humidity": [86, 84, 82, 78, 76, 74, 72, 74, 78, 82, 86, 88],
    },
}


def get_weather_for_region(region: str) -> dict:
    """
    Retourne les données météo mensuelles pour une région suisse.

    Données :
    - temps : température extérieure moyenne mensuelle [°C]
    - ground : température moyenne du sol [°C]
    - humidity : humidité relative moyenne [%]
    """

    if region in WEATHER_DATA:
        return WEATHER_DATA[region]

    # Fallback par défaut
    return WEATHER_DATA["Vaud"]