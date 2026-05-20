# app/services/materials.py

MATERIAL_PROPERTIES = {
    "Pierre": {"lambda": 1.8, "default_thickness_m": 0.60, "inertia_factor": 0.75},
    "Brique": {"lambda": 0.7, "default_thickness_m": 0.35, "inertia_factor": 0.90},
    "Béton": {"lambda": 1.7, "default_thickness_m": 0.40, "inertia_factor": 0.85},
    "Bois": {"lambda": 0.13, "default_thickness_m": 0.20, "inertia_factor": 0.95},
    "Métal-bois": {"lambda": 0.30, "default_thickness_m": 0.20, "inertia_factor": 1.00},
    "Panneau isolé": {"lambda": 0.025, "default_thickness_m": 0.16, "inertia_factor": 0.80},
    "Terre battue": {"lambda": 1.5, "default_thickness_m": 0.50, "inertia_factor": 0.70},
    "Dalle isolée": {"lambda": 0.04, "default_thickness_m": 0.30, "inertia_factor": 0.75},
}


def calculate_u_value(lambda_w_mk: float, thickness_m: float) -> float:
    rsi = 0.13
    rse = 0.04

    if not lambda_w_mk or not thickness_m:
        return 1.4

    r_total = rsi + (thickness_m / lambda_w_mk) + rse
    return round(1 / r_total, 2)


def get_material_properties(material: str) -> dict:
    props = MATERIAL_PROPERTIES.get(
        material,
        {"lambda": 0.7, "default_thickness_m": 0.35, "inertia_factor": 1.00},
    )

    return {
        **props,
        "default_u_value": calculate_u_value(
            props["lambda"],
            props["default_thickness_m"],
        ),
    }