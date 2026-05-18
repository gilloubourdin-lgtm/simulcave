# app/services/weather.py

SWISS_MONTHLY_WEATHER = {
    "romandie": {
        "label": "Romandie",
        "temps": [2, 4, 7, 11, 15, 19, 22, 21, 17, 12, 7, 3],
    },
    "arc_lemanique": {
        "label": "Arc lémanique",
        "temps": [3, 5, 8, 12, 16, 20, 23, 22, 18, 13, 8, 4],
    },
    "valais": {
        "label": "Valais",
        "temps": [1, 4, 8, 13, 17, 21, 24, 23, 18, 13, 7, 2],
    },
    "tessin": {
        "label": "Tessin",
        "temps": [5, 7, 11, 15, 19, 23, 26, 25, 21, 16, 10, 6],
    },
    "suisse_alemanique": {
        "label": "Suisse alémanique",
        "temps": [1, 3, 7, 11, 15, 19, 22, 21, 17, 11, 6, 2],
    },
    "alpes": {
        "label": "Alpes",
        "temps": [-3, -2, 2, 6, 10, 14, 17, 16, 12, 7, 2, -2],
    },
}


MONTHS = [
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]


HOURS_PER_MONTH = [
    31 * 24,
    28 * 24,
    31 * 24,
    30 * 24,
    31 * 24,
    30 * 24,
    31 * 24,
    31 * 24,
    30 * 24,
    31 * 24,
    30 * 24,
    31 * 24,
]


def get_weather_for_region(region: str):
    return SWISS_MONTHLY_WEATHER.get(
        region,
        SWISS_MONTHLY_WEATHER["romandie"],
    )