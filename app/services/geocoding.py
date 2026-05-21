import requests


def geocode_address(address: str):
    try:
        url = "https://nominatim.openstreetmap.org/search"

        params = {
            "q": address,
            "format": "json",
            "limit": 1,
        }

        headers = {
            "User-Agent": "SimulCave"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10,
        )

        data = response.json()

        if not data:
            return None

        return {
            "latitude": float(data[0]["lat"]),
            "longitude": float(data[0]["lon"]),
        }

    except Exception:
        return None