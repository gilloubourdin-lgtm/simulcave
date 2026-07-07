# app/services/nrcave_import.py

from app.models import Cave, Wall, Zone, ZoneMonthlyTarget
from app.services.materials import get_material_properties


def _safe_float(value, default=0.0):
    try:
        return float(value if value is not None else default)
    except Exception:
        return default


def _safe_int(value, default=1):
    try:
        return int(value if value is not None else default)
    except Exception:
        return default


def import_nrcave_project(payload: dict, db):
    data = payload.get("cave", {}) or {}
    building = payload.get("building", {}) or {}
    geometry = building.get("geometry", {}) or {}

    length = _safe_float(geometry.get("length_m"), 20)
    width = _safe_float(geometry.get("width_m"), 10)
    height = _safe_float(geometry.get("height_m"), 4)
    zone_count = max(1, _safe_int(building.get("thermal", {}).get("zones"), 1))

    cave = Cave(
        name=data.get("name") or "Cave importée NRCave",
        user_id=37,
        region=data.get("region") or data.get("canton") or "Vaud",
        address=data.get("address"),
        altitude_m=_safe_float(data.get("altitude_m"), 400),
        length_m=length,
        width_m=width,
        height_m=height,
        buried_factor=0.5,
        energy_source="electricity",
        energy_price_chf_per_kwh=0.25,
        co2_factor_kg_per_kwh=0.09,
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        use_dynamic_weather=True,
        ventilation_enabled=True,
        ventilation_rate_ach=0.10,
    )

    db.add(cave)
    db.flush()

    wall_material = building.get("wall", {}).get("material") or "Béton"
    roof_material = building.get("roof", {}).get("material") or "Béton"
    floor_material = building.get("floor", {}).get("material") or "Béton"

    wall_u = _safe_float(building.get("wall", {}).get("u_value"), 1.4)
    roof_u = _safe_float(building.get("roof", {}).get("u_value"), 0.8)
    floor_u = _safe_float(building.get("floor", {}).get("u_value"), 0.6)

    walls = [
        ("Mur Nord", "N", wall_material, length * height, wall_u),
        ("Mur Sud", "S", wall_material, length * height, wall_u),
        ("Mur Est", "E", wall_material, width * height, wall_u),
        ("Mur Ouest", "O", wall_material, width * height, wall_u),
        ("Toiture", "H", roof_material, length * width, roof_u),
        ("Sol", "B", floor_material, length * width, floor_u),
    ]

    for name, orientation, material, area, u_value in walls:
        props = get_material_properties(material)

        db.add(Wall(
            cave_id=cave.id,
            name=name,
            orientation=orientation,
            material=material,
            area_m2=area,
            u_value=u_value,
            thickness_m=props["default_thickness_m"],
            inertia_factor=props["inertia_factor"],
        ))

    default_monthly_profile = {
        1: (10, 75, "FML / stabilisation"),
        2: (10, 75, "Stabilisation"),
        3: (12, 75, "Stockage"),
        4: (12, 75, "Stockage"),
        5: (13, 75, "Stockage"),
        6: (14, 75, "Été"),
        7: (16, 75, "Été"),
        8: (16, 75, "Été"),
        9: (13, 75, "Refroidissement FA"),
        10: (10, 75, "FA / FML"),
        11: (8, 75, "Refroidissement FA"),
        12: (8, 75, "FML"),
    }

    total_volume = length * width * height
    zone_volume = total_volume / zone_count
    zone_length = length / zone_count

    for i in range(zone_count):
        zone = Zone(
            cave_id=cave.id,
            name=f"Zone {i + 1}",
            volume_m3=zone_volume,
            target_temp_winter_c=12,
            target_temp_summer_c=16,
            target_humidity_percent=75,
            process_cooling_kwh=0,
            process_heating_kwh=0,
            x_m=i * zone_length,
            y_m=0,
            width_m=width,
            length_m=zone_length,
            process_heating_start_month=1,
            process_heating_end_month=12,
            process_cooling_start_month=1,
            process_cooling_end_month=12,
        )

        db.add(zone)
        db.flush()

        for month, values in default_monthly_profile.items():
            temp, humidity, phase = values

            db.add(ZoneMonthlyTarget(
                zone_id=zone.id,
                month=month,
                target_temp_c=temp,
                target_humidity_percent=humidity,
                phase=phase,
            ))

    db.commit()
    db.refresh(cave)

    return cave