# SimulCave

SimulCave est une application FastAPI destinée à modéliser les besoins énergétiques, carbone et économiques des caves viticoles.

## Fonctionnalités

- Modélisation de caves viticoles
- Parois avec orientation, matériau, valeur U et inertie
- Zones thermiques avec températures et humidité cibles
- Simulation mensuelle chaud/froid
- Météo régionale suisse
- Coûts énergétiques
- Émissions CO₂
- Scénarios de rénovation
- Export PDF
- Authentification multi-utilisateurs
- Vue en plan 2D

## Stack

- FastAPI
- Jinja2
- SQLAlchemy
- PostgreSQL
- Render
- Chart.js
- WeasyPrint

## Lancement local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

## Arborescence du projet

```text
SimulCave/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── cave.py
│   │   └── auth.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── simulation.py
│   │   ├── renovation.py
│   │   ├── weather.py
│   │   ├── materials.py
│   │   ├── energy_factors.py
│   │   ├── pdf.py
│   │   └── auth.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── caves_list.html
│   │   ├── cave_form.html
│   │   ├── cave_detail.html
│   │   ├── cave_plan.html
│   │   ├── cave_parameters.html
│   │   ├── simulation_result.html
│   │   ├── renovation_result.html
│   │   ├── renovation_custom_form.html
│   │   ├── renovation_custom_result.html
│   │   ├── report_template.html
│   │   ├── login.html
│   │   └── register.html
│   │
│   └── static/
│       └── style.css
│
├── requirements.txt
├── Aptfile
├── README.md
└── .gitignore