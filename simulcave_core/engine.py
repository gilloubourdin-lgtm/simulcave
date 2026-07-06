def run_simulation(data: dict) -> dict:
    """
    Point d'entrée public du moteur SimulCave.
    Aucun FastAPI, aucun HTML, aucune base SQL ici.
    """

    surface_m2 = float(data.get("surface_m2") or 0)
    production_hl = float(data.get("production_hl") or 0)
    electricity_kwh = float(data.get("total_electricity_kwh") or 0)
    heating_kwh = float(data.get("heating_kwh") or 0)

    cooling_kwh = electricity_kwh * 0.35
    ecs_kwh = production_hl * 4.0

    return {
        "source": "simulcave_core",
        "profile_available": True,
        "annual_heating_kwh": round(heating_kwh, 0),
        "annual_cooling_kwh": round(cooling_kwh, 0),
        "annual_ecs_kwh": round(ecs_kwh, 0),
        "annual_electricity_kwh": round(electricity_kwh, 0),
        "input_summary": {
            "surface_m2": surface_m2,
            "production_hl": production_hl,
        },
    }