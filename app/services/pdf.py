# app/services/pdf.py

from pathlib import Path

from fastapi.templating import Jinja2Templates
from weasyprint import HTML

from app.services.simulation import simulate_cave
from app.services.renovation import generate_renovation_scenarios

templates = Jinja2Templates(directory="app/templates")


def generate_cave_report_pdf(request, cave) -> bytes:
    simulation = simulate_cave(cave)
    scenarios = generate_renovation_scenarios(cave)

    template = templates.get_template("report_pdf.html")

    html_content = template.render(
        request=request,
        cave=cave,
        simulation=simulation,
        scenarios=scenarios,
    )

    base_url = Path(".").resolve().as_uri()

    pdf = HTML(
        string=html_content,
        base_url=base_url,
    ).write_pdf()

    return pdf