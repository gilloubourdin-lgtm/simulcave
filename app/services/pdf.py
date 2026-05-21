# app/services/pdf.py

from pathlib import Path

from fastapi.templating import Jinja2Templates
from weasyprint import HTML

from app.services.simulation import simulate_cave
from app.services.renovation import (
    generate_renovation_scenarios,
    calculate_scenario,
)

templates = Jinja2Templates(directory="app/templates")


def calculate_saved_scenarios(cave):
    saved_scenarios_results = []

    for saved in cave.renovation_scenarios:
        reductions = []

        if saved.roof_reduction_percent > 0:
            reductions.append(saved.roof_reduction_percent)

        if saved.walls_reduction_percent > 0:
            reductions.append(saved.walls_reduction_percent)

        if saved.floor_reduction_percent > 0:
            reductions.append(saved.floor_reduction_percent)

        average_reduction_percent = sum(reductions) / len(reductions) if reductions else 0
        reduction_factor = 1 - (average_reduction_percent / 100)

        def wall_filter(wall, saved=saved):
            if wall.name == "Toiture" and saved.roof_reduction_percent > 0:
                return True

            if wall.orientation in ["N", "S", "E", "O"] and saved.walls_reduction_percent > 0:
                return True

            if wall.name == "Sol" and saved.floor_reduction_percent > 0:
                return True

            return False

        calculated = calculate_scenario(
            cave=cave,
            name=saved.name,
            description=(
                f"Toiture: -{saved.roof_reduction_percent} %, "
                f"murs: -{saved.walls_reduction_percent} %, "
                f"sol: -{saved.floor_reduction_percent} %."
            ),
            investment_chf=saved.investment_chf,
            wall_filter=wall_filter,
            reduction_factor=reduction_factor,
        )

        saved_scenarios_results.append({
            "saved": saved,
            "calculated": calculated,
        })

    return saved_scenarios_results


def generate_cave_report_pdf(request, cave) -> bytes:
    simulation = simulate_cave(cave)
    scenarios = generate_renovation_scenarios(cave)
    saved_scenarios_results = calculate_saved_scenarios(cave)

    template = templates.get_template("report_pdf.html")

    html_content = template.render(
        request=request,
        cave=cave,
        simulation=simulation,
        scenarios=scenarios,
        saved_scenarios_results=saved_scenarios_results,
    )

    base_url = Path(".").resolve().as_uri()

    pdf = HTML(
        string=html_content,
        base_url=base_url,
    ).write_pdf()

    return pdf