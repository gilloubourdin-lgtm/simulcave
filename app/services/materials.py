# app/services/materials.py

MATERIAL_INERTIA = {
    "Pierre": {
        "default_thickness_m": 0.60,
        "inertia_factor": 0.75,
        "default_u_value": 1.8,
    },
    "Brique": {
        "default_thickness_m": 0.35,
        "inertia_factor": 0.90,
        "default_u_value": 1.4,
    },
    "Béton": {
        "default_thickness_m": 0.40,
        "inertia_factor": 0.85,
        "default_u_value": 1.7,
    },
    "Bois": {
        "default_thickness_m": 0.20,
        "inertia_factor": 0.95,
        "default_u_value": 0.8,
    },
    "Métal-bois": {
        "default_thickness_m": 0.20,
        "inertia_factor": 1.00,
        "default_u_value": 1.2,
    },
    "Panneau isolé": {
        "default_thickness_m": 0.16,
        "inertia_factor": 0.80,
        "default_u_value": 0.25,
    },
    "Terre battue": {
        "default_thickness_m": 0.50,
        "inertia_factor": 0.70,
        "default_u_value": 1.5,
    },
    "Dalle isolée": {
        "default_thickness_m": 0.30,
        "inertia_factor": 0.75,
        "default_u_value": 0.35,
    },
}


def get_material_properties(material: str) -> dict:
    return MATERIAL_INERTIA.get(
        material,
        {
            "default_thickness_m": 0.30,
            "inertia_factor": 1.00,
            "default_u_value": 1.4,
        }
    )