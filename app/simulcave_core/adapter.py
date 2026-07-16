# app/simulcave_core/adapter.py

from __future__ import annotations

from typing import Any

from app.simulcave_core.engine import run_simulation


def simulate_from_dict(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Adaptateur public du moteur SimulCave.

    Il valide que l'entrée est bien un dictionnaire puis délègue
    le calcul au moteur indépendant de FastAPI et SQLAlchemy.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Les données transmises au moteur SimulCave "
            "doivent être un objet JSON."
        )

    return run_simulation(data)