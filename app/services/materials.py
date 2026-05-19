# app/services/materials.py

MATERIAL_INERTIA = {
    "Pierre": {
        "default_thickness_m": 0.60,
        "inertia_factor": 0.75,
    },
    "Brique": {
        "default_thickness_m": 0.35,
        "inertia_factor": 0.90,
    },
    "Béton": {
        "default_thickness_m": 0.40,
        "inertia_factor": 0.85,
    },
    "Bois": {
        "default_thickness_m": 0.20,
        "inertia_factor": 0.95,
    },
    "Métal-bois": {
        "default_thickness_m": 0.20,
        "inertia_factor": 1.00,
    },
    "Panneau isolé": {
        "default_thickness_m": 0.16,
        "inertia_factor": 0.80,
    },
    "Terre battue": {
        "default_thickness_m": 0.50,
        "inertia_factor": 0.70,
    },
    "Dalle isolée": {
        "default_thickness_m": 0.30,
        "inertia_factor": 0.75,
    },
}


def get_material_properties(material: str) -> dict:
    return MATERIAL_INERTIA.get(
        material,
        {
            "default_thickness_m": 0.30,
            "inertia_factor": 1.00,
        },
    )