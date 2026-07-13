# app/services/nrcave_import.py

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from app.models import (
    Cave,
    Wall,
    Zone,
    ZoneMonthlyTarget,
)
from app.services.materials import (
    get_material_properties,
)


DEFAULT_MONTHLY_PROFILE = {
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


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value in (None, ""):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _safe_int(
    value: Any,
    default: int = 1,
) -> int:
    try:
        if value in (None, ""):
            return default

        return int(value)

    except (TypeError, ValueError):
        return default


def _service_user_id() -> int:
    """
    Utilisateur SimulCave propriétaire des projets créés par NRCave.

    À définir sur Render avec :
    SIMULCAVE_NRCAVE_USER_ID=1
    """

    return max(
        1,
        _safe_int(
            os.getenv(
                "SIMULCAVE_NRCAVE_USER_ID",
                "1",
            ),
            1,
        ),
    )


def _source_identifiers(
    payload: dict,
) -> tuple[int | None, str | None, str]:
    cave_data = payload.get("cave", {}) or {}

    source_cave_id = (
        payload.get("source_cave_id")
        or cave_data.get("id")
    )

    source_cave_id = (
        _safe_int(source_cave_id, 0)
        if source_cave_id not in (None, "")
        else None
    )

    if source_cave_id == 0:
        source_cave_id = None

    site_key = (
        payload.get("source_site_key")
        or cave_data.get("site_key")
    )

    if site_key is not None:
        site_key = str(site_key).strip() or None

    instance = str(
        payload.get("source_instance")
        or "production"
    ).strip()

    if not instance:
        instance = "production"

    return (
        source_cave_id,
        site_key,
        instance,
    )


def _get_or_create_cave(
    *,
    payload: dict,
    db,
) -> tuple[Cave, bool]:
    """
    Recherche une cave SimulCave déjà liée à NRCave.

    Si elle n'existe pas, crée uniquement l'objet Python.
    Aucun flush SQL ne doit avoir lieu ici.
    """

    (
        source_cave_id,
        site_key,
        instance,
    ) = _source_identifiers(payload)

    cave = None

    if source_cave_id is not None:
        cave = (
            db.query(Cave)
            .filter(
                Cave.nrcave_instance == instance,
                Cave.nrcave_cave_id == source_cave_id,
            )
            .first()
        )

    if cave is None and site_key:
        cave = (
            db.query(Cave)
            .filter(
                Cave.nrcave_instance == instance,
                Cave.nrcave_site_key == site_key,
            )
            .first()
        )

    created = cave is None

    if created:
        cave = Cave(
            user_id=_service_user_id(),

            # Champs obligatoires provisoires.
            # Ils seront remplacés dans import_nrcave_project()
            # avant le premier db.flush().
            name="Cave importée NRCave",
            length_m=20.0,
            width_m=10.0,
            height_m=4.0,

            region="Vaud",
            altitude_m=500.0,
            buried_factor=0.5,

            ventilation_enabled=True,
            ventilation_rate_ach=0.2,

            energy_source="electricity",
            energy_price_chf_per_kwh=0.24,
            co2_factor_kg_per_kwh=0.09,
        )

        db.add(cave)

        # IMPORTANT :
        # aucun db.flush() ici.

    cave.nrcave_cave_id = source_cave_id
    cave.nrcave_site_key = site_key
    cave.nrcave_instance = instance
    cave.nrcave_last_sync_at = datetime.now(UTC)
    cave.nrcave_schema_version = str(
        payload.get("schema_version")
        or payload.get("version")
        or "legacy"
    )

    return cave, created


def _fallback_envelope(
    *,
    building: dict,
    length: float,
    width: float,
    height: float,
) -> list[dict]:
    wall_data = building.get("wall", {}) or {}
    roof_data = building.get("roof", {}) or {}
    floor_data = building.get("floor", {}) or {}

    wall_material = (
        wall_data.get("material")
        or "Béton"
    )

    roof_material = (
        roof_data.get("material")
        or "Béton"
    )

    floor_material = (
        floor_data.get("material")
        or "Béton"
    )

    wall_u = _safe_float(
        wall_data.get("u_value"),
        1.4,
    )

    roof_u = _safe_float(
        roof_data.get("u_value"),
        0.8,
    )

    floor_u = _safe_float(
        floor_data.get("u_value"),
        0.6,
    )

    return [
        {
            "name": "Mur Nord",
            "orientation": "N",
            "material": wall_material,
            "area_m2": length * height,
            "u_value": wall_u,
        },
        {
            "name": "Mur Sud",
            "orientation": "S",
            "material": wall_material,
            "area_m2": length * height,
            "u_value": wall_u,
        },
        {
            "name": "Mur Est",
            "orientation": "E",
            "material": wall_material,
            "area_m2": width * height,
            "u_value": wall_u,
        },
        {
            "name": "Mur Ouest",
            "orientation": "O",
            "material": wall_material,
            "area_m2": width * height,
            "u_value": wall_u,
        },
        {
            "name": "Toiture",
            "orientation": "H",
            "material": roof_material,
            "area_m2": length * width,
            "u_value": roof_u,
        },
        {
            "name": "Sol",
            "orientation": "B",
            "material": floor_material,
            "area_m2": length * width,
            "u_value": floor_u,
        },
    ]


def _sync_envelope(
    *,
    cave: Cave,
    envelope: list[dict],
    db,
) -> None:
    """
    Met à jour les parois portant le même nom.

    Les parois complémentaires créées manuellement dans SimulCave
    ne sont pas supprimées.
    """

    existing_by_name = {
        str(wall.name or "").strip(): wall
        for wall in (cave.walls or [])
        if str(wall.name or "").strip()
    }

    for index, wall_data in enumerate(envelope):
        name = str(
            wall_data.get("name")
            or f"Paroi {index + 1}"
        ).strip()

        orientation = str(
            wall_data.get("orientation")
            or "N"
        ).strip()

        material = (
            wall_data.get("label")
            or wall_data.get("material")
            or "Béton"
        )

        material = str(material).strip()

        props = (
            get_material_properties(material)
            or get_material_properties("Béton")
            or {}
        )

        wall = existing_by_name.get(name)

        if wall is None:
            wall = Wall(
                cave_id=cave.id,
                name=name,
            )
            db.add(wall)
            existing_by_name[name] = wall

        wall.orientation = orientation
        wall.material = material
        wall.area_m2 = _safe_float(
            wall_data.get("area_m2"),
            0.0,
        )
        wall.u_value = _safe_float(
            wall_data.get("u_value"),
            1.0,
        )
        wall.thickness_m = _safe_float(
            wall_data.get("thickness_m"),
            _safe_float(
                props.get(
                    "default_thickness_m"
                ),
                0.40,
            ),
        )
        wall.inertia_factor = _safe_float(
            wall_data.get("inertia_factor"),
            _safe_float(
                props.get("inertia_factor"),
                1.0,
            ),
        )


def _create_default_monthly_targets(
    *,
    zone: Zone,
    db,
) -> None:
    existing_months = {
        target.month
        for target in (
            zone.monthly_targets or []
        )
    }

    for month, values in DEFAULT_MONTHLY_PROFILE.items():
        if month in existing_months:
            continue

        temperature, humidity, phase = values

        db.add(
            ZoneMonthlyTarget(
                zone_id=zone.id,
                month=month,
                target_temp_c=temperature,
                target_humidity_percent=humidity,
                phase=phase,
            )
        )


def _create_default_zones_if_missing(
    *,
    cave: Cave,
    zone_count: int,
    length: float,
    width: float,
    height: float,
    db,
) -> bool:
    """
    Les zones existantes ne sont pas écrasées lors d'une synchronisation.

    Cela protège les réglages détaillés réalisés directement dans
    l'application SimulCave.
    """

    if cave.zones:
        for zone in cave.zones:
            _create_default_monthly_targets(
                zone=zone,
                db=db,
            )

        return False

    total_volume = length * width * height
    zone_volume = total_volume / zone_count
    zone_length = length / zone_count

    for index in range(zone_count):
        zone = Zone(
            cave_id=cave.id,
            name=f"Zone {index + 1}",
            volume_m3=zone_volume,
            target_temp_winter_c=12,
            target_temp_summer_c=16,
            target_humidity_percent=75,
            process_cooling_kwh=0,
            process_heating_kwh=0,
            x_m=index * zone_length,
            y_m=0,
            width_m=width,
            length_m=zone_length,
            level_index=0,
            level_name="Rez",
            floor_depth_m=0.0,
            process_heating_start_month=1,
            process_heating_end_month=12,
            process_cooling_start_month=1,
            process_cooling_end_month=12,
        )

        db.add(zone)
        db.flush()

        _create_default_monthly_targets(
            zone=zone,
            db=db,
        )

    return True


def import_nrcave_project(
    payload: dict,
    db,
) -> tuple[Cave, bool, list[str]]:
    """
    Crée ou met à jour un projet SimulCave lié à NRCave.

    Retour :
        cave
        created
        warnings
    """

    if not isinstance(payload, dict):
        raise ValueError(
            "Le payload NRCave doit être un objet JSON."
        )

    cave_data = payload.get("cave", {}) or {}
    building = payload.get("building", {}) or {}
    geometry = building.get("geometry", {}) or {}
    thermal = building.get("thermal", {}) or {}

    length = max(
        0.1,
        _safe_float(
            geometry.get("length_m"),
            20.0,
        ),
    )

    width = max(
        0.1,
        _safe_float(
            geometry.get("width_m"),
            10.0,
        ),
    )

    height = max(
        0.1,
        _safe_float(
            geometry.get("height_m"),
            4.0,
        ),
    )

    zone_count = max(
        1,
        _safe_int(
            thermal.get("zones"),
            1,
        ),
    )

    cave, created = _get_or_create_cave(
        payload=payload,
        db=db,
    )

    warnings: list[str] = []

    cave.name = (
        cave_data.get("name")
        or cave.name
        or "Cave importée NRCave"
    )

    cave.region = (
        cave_data.get("region")
        or cave_data.get("canton")
        or cave.region
        or "Vaud"
    )

    cave.address = (
        cave_data.get("address")
        or cave.address
    )

    cave.altitude_m = _safe_float(
        cave_data.get("altitude_m"),
        _safe_float(
            cave.altitude_m,
            400.0,
        ),
    )

    cave.length_m = length
    cave.width_m = width
    cave.height_m = height

    cave.latitude = cave_data.get(
        "latitude"
    )

    cave.longitude = cave_data.get(
        "longitude"
    )

    cave.use_dynamic_weather = bool(
        cave.latitude is not None
        and cave.longitude is not None
    )

    # La valeur peut maintenant être fournie par NRCave.
    # Sinon, on conserve l'existant ou le fallback 0.5.
    cave.buried_factor = _safe_float(
        building.get("buried_factor"),
        _safe_float(
            cave.buried_factor,
            0.5,
        ),
    )

    ventilation = (
        building.get("ventilation", {})
        or {}
    )

    cave.ventilation_enabled = bool(
        ventilation.get(
            "enabled",
            cave.ventilation_enabled
            if cave.ventilation_enabled is not None
            else True,
        )
    )

    cave.ventilation_rate_ach = _safe_float(
        ventilation.get("rate_ach"),
        _safe_float(
            cave.ventilation_rate_ach,
            0.10,
        ),
    )

    energy = (
        payload.get("energy", {})
        or {}
    )

    cave.energy_source = (
        energy.get("source")
        or cave.energy_source
        or "electricity"
    )

    cave.energy_price_chf_per_kwh = _safe_float(
        energy.get("price_per_kwh"),
        _safe_float(
            cave.energy_price_chf_per_kwh,
            0.25,
        ),
    )

    cave.co2_factor_kg_per_kwh = _safe_float(
        energy.get("co2_factor_kg_per_kwh"),
        _safe_float(
            cave.co2_factor_kg_per_kwh,
            0.09,
        ),
    )

    db.flush()
    db.refresh(cave)

    envelope = (
        building.get("envelope", [])
        or []
    )

    if not envelope:
        envelope = _fallback_envelope(
            building=building,
            length=length,
            width=width,
            height=height,
        )

        warnings.append(
            "L’enveloppe détaillée était absente : "
            "des parois par défaut ont été générées."
        )

    _sync_envelope(
        cave=cave,
        envelope=envelope,
        db=db,
    )

    zones_created = _create_default_zones_if_missing(
        cave=cave,
        zone_count=zone_count,
        length=length,
        width=width,
        height=height,
        db=db,
    )

    if not zones_created and len(cave.zones or []) != zone_count:
        warnings.append(
            (
                f"NRCave indique {zone_count} zone(s), mais le projet "
                f"SimulCave en contient déjà {len(cave.zones or [])}. "
                "Les zones SimulCave existantes ont été conservées."
            )
        )

    db.commit()
    db.refresh(cave)

    return cave, created, warnings